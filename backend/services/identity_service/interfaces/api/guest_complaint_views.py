from datetime import timedelta

from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.services.audit_logging import AuditContext
from application.services.guest_complaints import (
    ComplaintFilters,
    ComplaintFollowUpService,
    ComplaintLifecycleService,
    ComplaintService,
    GuestComplaintNotFoundError,
    GuestComplaintTransitionError,
    GuestComplaintValidationError,
    GuestExperienceAnalyticsService,
    ResolutionConfirmationService,
)
from infrastructure.db.core.models import GuestComplaint, GuestComplaintFollowUp, RolePermission, User, UserRole
from infrastructure.services.audit_logging import get_audit_logger
from interfaces.api.serializers import (
    GuestComplaintAssignSerializer,
    GuestComplaintCreateSerializer,
    GuestComplaintEscalateSerializer,
    GuestComplaintFollowUpCompleteSerializer,
    GuestComplaintFollowUpCreateSerializer,
    GuestComplaintResolutionConfirmSerializer,
    GuestComplaintResponseSerializer,
    GuestComplaintTransitionSerializer,
    GuestComplaintUpdateSerializer,
)


def _has_permission(user, code: str) -> bool:
    if not user:
        return False
    if hasattr(user, "is_authenticated") and not user.is_authenticated:
        return False
    if UserRole.objects.filter(user=user, role__name__iexact="super admin").exists():
        return True
    return RolePermission.objects.filter(role__user_roles__user=user, permission__code=code).exists()


def _audit_context(request, org_id: int, actor_user=None) -> AuditContext:
    if hasattr(request, "audit_context"):
        meta = request.audit_context
        return AuditContext(
            org_id=org_id,
            property_id=None,
            actor_user_id=getattr(actor_user, "id", None),
            ip_address=meta.get("ip_address", ""),
            user_agent=meta.get("user_agent", ""),
        )
    return AuditContext(
        org_id=org_id,
        property_id=None,
        actor_user_id=getattr(actor_user, "id", None),
        ip_address=request.META.get("REMOTE_ADDR", ""),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )


def _audit_action(request, *, org_id: int, action: str, target_id: str, metadata: dict, actor_user=None):
    get_audit_logger().log_action(
        action=action,
        target_type="guest_complaint",
        target_id=str(target_id),
        metadata=metadata,
        context=_audit_context(request, org_id, actor_user=actor_user),
    )


def _to_dict(c: GuestComplaint) -> dict:
    return {
        "id": c.id,
        "complaint_number": c.complaint_number,
        "org_id": c.org_id,
        "guest_id": c.guest_id,
        "guest_name": c.guest_name,
        "guest_contact": c.guest_contact,
        "property_id": c.property_id,
        "room_id": c.room_id,
        "department_id": c.department_id,
        "category": c.category,
        "severity": c.severity,
        "status": c.status,
        "title": c.title,
        "description": c.description,
        "source": c.source,
        "vip_guest": c.vip_guest,
        "reported_at": c.reported_at,
        "shift": c.shift,
        "assigned_to": c.assigned_to_id,
        "escalated_to": c.escalated_to_id,
        "due_at": c.due_at,
        "resolved_at": c.resolved_at,
        "confirmed_at": c.confirmed_at,
        "satisfaction_score": c.satisfaction_score,
        "satisfaction_comment": c.satisfaction_comment,
        "created_by": c.created_by_id,
        "updated_by": c.updated_by_id,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


class GuestComplaintListCreateView(APIView):
    service = ComplaintService()

    def post(self, request):
        if not _has_permission(request.user, "guest_complaints.manage"):
            return Response({"detail": "Permission required: guest_complaints.manage"}, status=status.HTTP_403_FORBIDDEN)
        ser = GuestComplaintCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        assignee = None
        if data.get("assigned_to"):
            assignee = User.objects.filter(id=data["assigned_to"], org_id=data["org_id"]).first()
        complaint, route_meta = self.service.create(
            created_by=request.user,
            org_id=data["org_id"],
            **{k: v for k, v in data.items() if k != "org_id"},
            assigned_to=assignee,
        )
        _audit_action(request, org_id=complaint.org_id, action="complaint_created", target_id=str(complaint.id), metadata={"routing": route_meta}, actor_user=request.user)
        return Response(GuestComplaintResponseSerializer(_to_dict(complaint)).data, status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "guest_complaints.view"):
            return Response({"detail": "Permission required: guest_complaints.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = request.query_params.get("org_id")
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        filters = ComplaintFilters(
            org_id=int(org_id),
            status=request.query_params.get("status"),
            severity=request.query_params.get("severity"),
            category=request.query_params.get("category"),
            source=request.query_params.get("source"),
            property_id=int(request.query_params["property"]) if request.query_params.get("property") else None,
            department_id=int(request.query_params["department"]) if request.query_params.get("department") else None,
            assigned_to=int(request.query_params["assigned_to"]) if request.query_params.get("assigned_to") else None,
            escalated_to=int(request.query_params["escalated_to"]) if request.query_params.get("escalated_to") else None,
            date_from=parse_date(request.query_params.get("date_from")) if request.query_params.get("date_from") else None,
            date_to=parse_date(request.query_params.get("date_to")) if request.query_params.get("date_to") else None,
        )
        qs = self.service.list(filters=filters)
        q = request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(complaint_number__icontains=q) | Q(guest_name__icontains=q))
        total = qs.count()
        page = max(int(request.query_params.get("page", 1)), 1)
        page_size = min(max(int(request.query_params.get("page_size", 10)), 1), 100)
        rows = qs.order_by("-created_at")[(page - 1) * page_size : (page - 1) * page_size + page_size]
        return Response({"count": total, "page": page, "page_size": page_size, "results": [GuestComplaintResponseSerializer(_to_dict(x)).data for x in rows]})


class GuestComplaintDetailView(APIView):
    service = ComplaintService()

    def get(self, request, complaint_id: int):
        if not _has_permission(request.user, "guest_complaints.view"):
            return Response({"detail": "Permission required: guest_complaints.view"}, status=status.HTTP_403_FORBIDDEN)
        try:
            row = self.service.get(complaint_id=complaint_id, org_id=int(request.query_params.get("org_id", "0")))
        except GuestComplaintNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(GuestComplaintResponseSerializer(_to_dict(row)).data)

    def patch(self, request, complaint_id: int):
        if not _has_permission(request.user, "guest_complaints.manage"):
            return Response({"detail": "Permission required: guest_complaints.manage"}, status=status.HTTP_403_FORBIDDEN)
        ser = GuestComplaintUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        try:
            row = self.service.get(complaint_id=complaint_id, org_id=int(request.data.get("org_id", 0)))
        except GuestComplaintNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        updated = self.service.update(complaint=row, actor=request.user, **ser.validated_data)
        _audit_action(request, org_id=updated.org_id, action="complaint_updated", target_id=str(updated.id), metadata={"status": updated.status}, actor_user=request.user)
        return Response(GuestComplaintResponseSerializer(_to_dict(updated)).data)


class GuestComplaintAssignView(APIView):
    service = ComplaintService()

    def post(self, request, complaint_id: int):
        if not _has_permission(request.user, "guest_complaints.manage"):
            return Response({"detail": "Permission required: guest_complaints.manage"}, status=status.HTTP_403_FORBIDDEN)
        ser = GuestComplaintAssignSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            complaint = self.service.get(complaint_id=complaint_id, org_id=ser.validated_data["org_id"])
        except GuestComplaintNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        assignee = User.objects.filter(id=ser.validated_data["assignee_id"], org_id=complaint.org_id).first()
        if not assignee:
            return Response({"detail": "Assignee not found in organization"}, status=status.HTTP_400_BAD_REQUEST)
        complaint = self.service.assign(complaint=complaint, assignee=assignee, actor=request.user, reason=ser.validated_data.get("reason", ""))
        _audit_action(request, org_id=complaint.org_id, action="complaint_assigned", target_id=str(complaint.id), metadata={"assignee_id": assignee.id}, actor_user=request.user)
        return Response(GuestComplaintResponseSerializer(_to_dict(complaint)).data)


class GuestComplaintTransitionView(APIView):
    target_status = ""
    service = ComplaintService()

    def post(self, request, complaint_id: int):
        if not _has_permission(request.user, "guest_complaints.manage"):
            return Response({"detail": "Permission required: guest_complaints.manage"}, status=status.HTTP_403_FORBIDDEN)
        ser = GuestComplaintTransitionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            complaint = self.service.get(complaint_id=complaint_id, org_id=ser.validated_data["org_id"])
            updated = self.service.lifecycle_service.transition(
                complaint=complaint,
                to_status=self.target_status,
                actor=request.user,
                reason=ser.validated_data.get("reason", ""),
            )
            if self.target_status == GuestComplaint.STATUS_RESOLVED and self.service.follow_up_service.requires_auto_follow_up(complaint=updated):
                self.service.follow_up_service.create_follow_up(
                    complaint=updated,
                    follow_up_type="POST_RESOLUTION",
                    scheduled_at=timezone.now() + timedelta(hours=24),
                    created_by=request.user,
                    assigned_to=updated.assigned_to,
                )
        except GuestComplaintNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except GuestComplaintTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit_action(request, org_id=updated.org_id, action="complaint_status_changed", target_id=str(updated.id), metadata={"status": updated.status}, actor_user=request.user)
        if self.target_status == GuestComplaint.STATUS_RESOLVED:
            _audit_action(request, org_id=updated.org_id, action="complaint_resolved", target_id=str(updated.id), metadata={}, actor_user=request.user)
        if self.target_status == GuestComplaint.STATUS_REOPENED:
            _audit_action(request, org_id=updated.org_id, action="complaint_reopened", target_id=str(updated.id), metadata={}, actor_user=request.user)
        if self.target_status == GuestComplaint.STATUS_VOID:
            _audit_action(request, org_id=updated.org_id, action="complaint_voided", target_id=str(updated.id), metadata={}, actor_user=request.user)
        if self.target_status == GuestComplaint.STATUS_CLOSED:
            _audit_action(request, org_id=updated.org_id, action="complaint_closed", target_id=str(updated.id), metadata={}, actor_user=request.user)
        return Response(GuestComplaintResponseSerializer(_to_dict(updated)).data)


class GuestComplaintStartView(GuestComplaintTransitionView):
    target_status = GuestComplaint.STATUS_IN_PROGRESS


class GuestComplaintResolveView(GuestComplaintTransitionView):
    target_status = GuestComplaint.STATUS_RESOLVED


class GuestComplaintReopenView(GuestComplaintTransitionView):
    target_status = GuestComplaint.STATUS_REOPENED


class GuestComplaintVoidView(GuestComplaintTransitionView):
    target_status = GuestComplaint.STATUS_VOID


class GuestComplaintEscalateView(APIView):
    service = ComplaintService()

    def post(self, request, complaint_id: int):
        if not _has_permission(request.user, "guest_complaints.manage"):
            return Response({"detail": "Permission required: guest_complaints.manage"}, status=status.HTTP_403_FORBIDDEN)
        ser = GuestComplaintEscalateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            complaint = self.service.get(complaint_id=complaint_id, org_id=ser.validated_data["org_id"])
        except GuestComplaintNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        escalated_to = None
        if ser.validated_data.get("escalated_to"):
            escalated_to = User.objects.filter(id=ser.validated_data["escalated_to"], org_id=complaint.org_id).first()
        done, flag = self.service.escalation_service.escalate(
            complaint=complaint,
            actor=request.user,
            reason=ser.validated_data["reason"],
            escalated_to=escalated_to,
            escalation_level=ser.validated_data.get("escalation_level", 1),
            manual=True,
        )
        if not done and flag == "invalid_transition":
            return Response({"detail": "Invalid transition for escalation"}, status=status.HTTP_400_BAD_REQUEST)
        _audit_action(request, org_id=complaint.org_id, action="complaint_escalated", target_id=str(complaint.id), metadata={"flag": flag}, actor_user=request.user)
        return Response({"status": "ok", "result": flag})


class GuestComplaintEscalationRunView(APIView):
    service = ComplaintService()

    def post(self, request):
        if not _has_permission(request.user, "guest_complaints.manage"):
            return Response({"detail": "Permission required: guest_complaints.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        summary = self.service.escalation_service.run_batch(org_id=org_id, actor=request.user)
        return Response(summary)


class GuestComplaintFollowUpListCreateView(APIView):
    service = ComplaintService()

    def post(self, request, complaint_id: int):
        if not _has_permission(request.user, "guest_complaints.manage"):
            return Response({"detail": "Permission required: guest_complaints.manage"}, status=status.HTTP_403_FORBIDDEN)
        ser = GuestComplaintFollowUpCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        complaint = self.service.get(complaint_id=complaint_id, org_id=ser.validated_data["org_id"])
        assignee = None
        if ser.validated_data.get("assigned_to"):
            assignee = User.objects.filter(id=ser.validated_data["assigned_to"], org_id=complaint.org_id).first()
        follow_up = self.service.follow_up_service.create_follow_up(
            complaint=complaint,
            follow_up_type=ser.validated_data["follow_up_type"],
            scheduled_at=ser.validated_data["scheduled_at"],
            assigned_to=assignee,
            notes=ser.validated_data.get("notes", ""),
            created_by=request.user,
        )
        _audit_action(request, org_id=complaint.org_id, action="follow_up_created", target_id=str(complaint.id), metadata={"follow_up_id": follow_up.id}, actor_user=request.user)
        return Response({"id": follow_up.id, "status": follow_up.status}, status=status.HTTP_201_CREATED)

    def get(self, request, complaint_id: int):
        if not _has_permission(request.user, "guest_complaints.view"):
            return Response({"detail": "Permission required: guest_complaints.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        self.service.get(complaint_id=complaint_id, org_id=org_id)
        rows = self.service.follow_up_service.repository.list(
            complaint_id=complaint_id,
            assigned_to=int(request.query_params["assigned_to"]) if request.query_params.get("assigned_to") else None,
            status=request.query_params.get("status"),
            date_from=parse_date(request.query_params.get("date_from")) if request.query_params.get("date_from") else None,
            date_to=parse_date(request.query_params.get("date_to")) if request.query_params.get("date_to") else None,
        ).order_by("-scheduled_at")
        return Response({
            "count": rows.count(),
            "results": [
                {
                    "id": x.id,
                    "complaint_id": x.complaint_id,
                    "follow_up_type": x.follow_up_type,
                    "scheduled_at": x.scheduled_at,
                    "completed_at": x.completed_at,
                    "assigned_to": x.assigned_to_id,
                    "notes": x.notes,
                    "status": x.status,
                    "created_by": x.created_by_id,
                    "created_at": x.created_at,
                    "updated_at": x.updated_at,
                }
                for x in rows
            ],
        })


class GuestComplaintFollowUpCompleteView(APIView):
    service = ComplaintService()

    def post(self, request, follow_up_id: int):
        if not _has_permission(request.user, "guest_complaints.manage"):
            return Response({"detail": "Permission required: guest_complaints.manage"}, status=status.HTTP_403_FORBIDDEN)
        ser = GuestComplaintFollowUpCompleteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        follow_up = GuestComplaintFollowUp.objects.filter(id=follow_up_id).first()
        if not follow_up:
            return Response({"detail": "Follow-up not found"}, status=status.HTTP_404_NOT_FOUND)
        updated = self.service.follow_up_service.complete_follow_up(follow_up=follow_up, notes=ser.validated_data.get("notes", ""))
        _audit_action(request, org_id=updated.complaint.org_id, action="follow_up_completed", target_id=str(updated.complaint_id), metadata={"follow_up_id": updated.id}, actor_user=request.user)
        return Response({"id": updated.id, "status": updated.status, "completed_at": updated.completed_at})


class GuestComplaintConfirmResolutionView(APIView):
    service = ComplaintService()
    confirmation = ResolutionConfirmationService()

    def post(self, request, complaint_id: int):
        if not _has_permission(request.user, "guest_complaints.manage"):
            return Response({"detail": "Permission required: guest_complaints.manage"}, status=status.HTTP_403_FORBIDDEN)
        ser = GuestComplaintResolutionConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            complaint = self.service.get(complaint_id=complaint_id, org_id=ser.validated_data["org_id"])
            updated = self.confirmation.confirm(
                complaint=complaint,
                actor=request.user,
                satisfaction_score=ser.validated_data["satisfaction_score"],
                satisfaction_comment=ser.validated_data.get("satisfaction_comment", ""),
            )
        except GuestComplaintNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except GuestComplaintValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except GuestComplaintTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit_action(request, org_id=updated.org_id, action="complaint_confirmed", target_id=str(updated.id), metadata={"score": str(updated.satisfaction_score)}, actor_user=request.user)
        return Response(GuestComplaintResponseSerializer(_to_dict(updated)).data)


class GuestComplaintAnalyticsSummaryView(APIView):
    analytics = GuestExperienceAnalyticsService()

    def get(self, request):
        if not _has_permission(request.user, "guest_complaints.view"):
            return Response({"detail": "Permission required: guest_complaints.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", 0))
        filters = ComplaintFilters(
            org_id=org_id,
            property_id=int(request.query_params["property"]) if request.query_params.get("property") else None,
            department_id=int(request.query_params["department"]) if request.query_params.get("department") else None,
            category=request.query_params.get("category"),
            severity=request.query_params.get("severity"),
            source=request.query_params.get("source"),
            date_from=parse_date(request.query_params.get("date_from")) if request.query_params.get("date_from") else None,
            date_to=parse_date(request.query_params.get("date_to")) if request.query_params.get("date_to") else None,
        )
        payload = self.analytics.summary(org_id=org_id, filters=filters)
        _audit_action(request, org_id=org_id, action="analytics_viewed", target_id="summary", metadata={"scope": "guest_complaints"}, actor_user=request.user)
        return Response(payload)


class GuestComplaintAnalyticsTrendsView(APIView):
    analytics = GuestExperienceAnalyticsService()

    def get(self, request):
        org_id = int(request.query_params.get("org_id", 0))
        filters = ComplaintFilters(org_id=org_id, date_from=parse_date(request.query_params.get("date_from")) if request.query_params.get("date_from") else None, date_to=parse_date(request.query_params.get("date_to")) if request.query_params.get("date_to") else None)
        return Response({"results": self.analytics.trends(org_id=org_id, filters=filters, group_by=request.query_params.get("group_by", "day"))})


class GuestComplaintAnalyticsResolutionTimeView(APIView):
    analytics = GuestExperienceAnalyticsService()

    def get(self, request):
        org_id = int(request.query_params.get("org_id", 0))
        filters = ComplaintFilters(org_id=org_id)
        return Response(self.analytics.resolution_time(org_id=org_id, filters=filters))


class GuestComplaintAnalyticsSatisfactionView(APIView):
    analytics = GuestExperienceAnalyticsService()

    def get(self, request):
        org_id = int(request.query_params.get("org_id", 0))
        filters = ComplaintFilters(org_id=org_id)
        return Response(self.analytics.satisfaction(org_id=org_id, filters=filters))


class GuestComplaintAuditLogView(APIView):
    def get(self, request):
        if not _has_permission(request.user, "audit.view"):
            return Response({"detail": "Permission required: audit.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = request.query_params.get("org_id")
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        from infrastructure.db.core.models import AuditLog

        qs = AuditLog.objects.filter(org_id=int(org_id), target_type="guest_complaint")
        if request.query_params.get("action"):
            qs = qs.filter(action__icontains=request.query_params["action"])
        if request.query_params.get("target_id"):
            qs = qs.filter(target_id=request.query_params["target_id"])
        rows = qs.order_by("-created_at")[:200]
        return Response({
            "count": qs.count(),
            "results": [
                {
                    "id": x.id,
                    "actor_id": x.actor_user_id,
                    "action": x.action,
                    "entity_type": x.target_type,
                    "entity_id": x.target_id,
                    "metadata": x.metadata_json,
                    "ip_address": x.ip_address,
                    "user_agent": x.user_agent,
                    "created_at": x.created_at,
                }
                for x in rows
            ],
        })
