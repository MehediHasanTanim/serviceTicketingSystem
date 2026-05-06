from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.services.audit_logging import AuditContext
from application.services.projects import (
    ProjectFilters,
    ProjectLifecycleService,
    ProjectNotFoundError,
    ProjectService,
    ProjectTransitionError,
    ProjectValidationError,
    SnaggingItemService,
    SnaggingTransitionError,
    TechnicalAuditService,
    TechnicalAuditTransitionError,
)
from infrastructure.db.core.models import Project, RolePermission, SnaggingItem, TechnicalAudit, User, UserRole
from infrastructure.services.audit_logging import get_audit_logger
from interfaces.api.serializers import (
    ProjectCreateSerializer,
    ProjectProgressUpdateSerializer,
    ProjectResponseSerializer,
    ProjectStatusUpdateSerializer,
    ProjectUpdateSerializer,
    SnaggingAssignSerializer,
    SnaggingCreateSerializer,
    SnaggingResponseSerializer,
    SnaggingTransitionSerializer,
    SnaggingUpdateSerializer,
    TechnicalAuditCompleteSerializer,
    TechnicalAuditCreateSerializer,
    TechnicalAuditResponseSerializer,
    TechnicalAuditUpdateSerializer,
)


def _has_permission(user, code: str) -> bool:
    if not user:
        return False
    if hasattr(user, "is_authenticated") and not user.is_authenticated:
        return False
    if UserRole.objects.filter(user=user, role__name__iexact="super admin").exists():
        return True
    return RolePermission.objects.filter(role__user_roles__user=user, permission__code=code).exists()


def _audit_context(request, *, org_id: int, property_id=None, actor=None):
    meta = getattr(request, "audit_context", {})
    return AuditContext(
        org_id=org_id,
        property_id=property_id,
        actor_user_id=getattr(actor, "id", None),
        ip_address=meta.get("ip_address", request.META.get("REMOTE_ADDR", "")),
        user_agent=meta.get("user_agent", request.META.get("HTTP_USER_AGENT", "")),
    )


def _audit(request, *, org_id: int, action: str, target_type: str, target_id: str, metadata=None, property_id=None, actor=None):
    try:
        get_audit_logger().log_action(
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            metadata=metadata or {},
            context=_audit_context(request, org_id=org_id, property_id=property_id, actor=actor),
        )
    except Exception:
        pass


def _project_dict(row: Project) -> dict:
    return {
        "id": row.id,
        "org_id": row.org_id,
        "project_code": row.project_code,
        "title": row.title,
        "description": row.description,
        "property_id": row.property_id,
        "department_id": row.department_id,
        "project_type": row.project_type,
        "priority": row.priority,
        "status": row.status,
        "owner_id": row.owner_id,
        "manager_id": row.manager_id,
        "start_date": row.start_date,
        "planned_end_date": row.planned_end_date,
        "actual_end_date": row.actual_end_date,
        "budget_amount": row.budget_amount,
        "actual_cost": row.actual_cost,
        "progress_percentage": row.progress_percentage,
        "created_by": row.created_by_id,
        "updated_by": row.updated_by_id,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _snag_dict(row: SnaggingItem) -> dict:
    return {
        "id": row.id,
        "snag_number": row.snag_number,
        "project_id": row.project_id,
        "title": row.title,
        "description": row.description,
        "category": row.category,
        "severity": row.severity,
        "status": row.status,
        "location_id": row.location_id,
        "room_id": row.room_id,
        "asset_id": row.asset_id,
        "assigned_to": row.assigned_to_id,
        "reported_by": row.reported_by_id,
        "due_at": row.due_at,
        "resolved_at": row.resolved_at,
        "verified_at": row.verified_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _audit_dict(row: TechnicalAudit) -> dict:
    return {
        "id": row.id,
        "audit_number": row.audit_number,
        "project_id": row.project_id,
        "title": row.title,
        "scope": row.scope,
        "auditor_id": row.auditor_id,
        "status": row.status,
        "result": row.result,
        "score": row.score,
        "findings_summary": row.findings_summary,
        "corrective_actions_required": row.corrective_actions_required,
        "conducted_at": row.conducted_at,
        "completed_at": row.completed_at,
        "created_by": row.created_by_id,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


class ProjectListCreateView(APIView):
    service = ProjectService()

    def post(self, request):
        if not _has_permission(request.user, "projects.manage"):
            return Response({"detail": "Permission required: projects.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            project = self.service.create(org_id=data["org_id"], actor=request.user, **{k: v for k, v in data.items() if k != "org_id"})
        except ProjectValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=project.org_id, action="project_created", target_type="project", target_id=str(project.id), metadata={"project_code": project.project_code}, property_id=project.property_id, actor=request.user)
        return Response(ProjectResponseSerializer(_project_dict(project)).data, status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "projects.view"):
            return Response({"detail": "Permission required: projects.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        filters = ProjectFilters(
            org_id=org_id,
            property_id=int(request.query_params["property"]) if request.query_params.get("property") else None,
            department_id=int(request.query_params["department"]) if request.query_params.get("department") else None,
            project_type=request.query_params.get("project_type"),
            status=request.query_params.get("status"),
            priority=request.query_params.get("priority"),
            owner_id=int(request.query_params["owner"]) if request.query_params.get("owner") else None,
            manager_id=int(request.query_params["manager"]) if request.query_params.get("manager") else None,
            q=request.query_params.get("q"),
        )
        if request.query_params.get("date_from"):
            from django.utils.dateparse import parse_date
            filters.date_from = parse_date(request.query_params.get("date_from"))
        if request.query_params.get("date_to"):
            from django.utils.dateparse import parse_date
            filters.date_to = parse_date(request.query_params.get("date_to"))
        qs = self.service.list(filters=filters)
        sort_by = request.query_params.get("sort_by", "created_at")
        sort_dir = request.query_params.get("sort_dir", "desc").lower()
        allowed = {"id", "project_code", "title", "status", "priority", "created_at", "updated_at", "start_date", "planned_end_date"}
        if sort_by not in allowed:
            sort_by = "created_at"
        prefix = "-" if sort_dir == "desc" else ""
        page = max(int(request.query_params.get("page", "1") or "1"), 1)
        page_size = min(max(int(request.query_params.get("page_size", "10") or "10"), 1), 100)
        total = qs.count()
        rows = qs.order_by(f"{prefix}{sort_by}")[(page - 1) * page_size: (page - 1) * page_size + page_size]
        return Response({"count": total, "page": page, "page_size": page_size, "results": [ProjectResponseSerializer(_project_dict(x)).data for x in rows]})


class ProjectDetailView(APIView):
    service = ProjectService()

    def get(self, request, project_id: int):
        if not _has_permission(request.user, "projects.view"):
            return Response({"detail": "Permission required: projects.view"}, status=status.HTTP_403_FORBIDDEN)
        try:
            row = self.service.get(project_id=project_id, org_id=int(request.query_params.get("org_id", "0")))
        except ProjectNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProjectResponseSerializer(_project_dict(row)).data)

    def patch(self, request, project_id: int):
        if not _has_permission(request.user, "projects.manage"):
            return Response({"detail": "Permission required: projects.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProjectUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            row = self.service.get(project_id=project_id, org_id=int(request.data.get("org_id", 0)))
            row = self.service.update(project=row, actor=request.user, **serializer.validated_data)
        except ProjectNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ProjectValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=row.org_id, action="project_updated", target_type="project", target_id=str(row.id), metadata={"status": row.status}, property_id=row.property_id, actor=request.user)
        return Response(ProjectResponseSerializer(_project_dict(row)).data)

    def delete(self, request, project_id: int):
        if not _has_permission(request.user, "projects.manage"):
            return Response({"detail": "Permission required: projects.manage"}, status=status.HTTP_403_FORBIDDEN)
        try:
            row = self.service.get(project_id=project_id, org_id=int(request.query_params.get("org_id", "0")))
            self.service.delete(project=row)
        except ProjectNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        _audit(request, org_id=row.org_id, action="project_voided", target_type="project", target_id=str(row.id), metadata={}, property_id=row.property_id, actor=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectStatusUpdateView(APIView):
    lifecycle = ProjectLifecycleService()
    project_service = ProjectService()

    def post(self, request, project_id: int):
        if not _has_permission(request.user, "projects.manage"):
            return Response({"detail": "Permission required: projects.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProjectStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            project = self.project_service.get(project_id=project_id, org_id=data["org_id"])
            updated = self.lifecycle.change_status(project=project, to_status=data["new_status"], actor=request.user, message=data.get("message", ""), admin_override=data.get("admin_override", False), actual_end_date=data.get("actual_end_date"))
        except (ProjectNotFoundError,) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except (ProjectTransitionError, ProjectValidationError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=updated.org_id, action="project_status_changed", target_type="project", target_id=str(updated.id), metadata={"status": updated.status}, property_id=updated.property_id, actor=request.user)
        if updated.status == Project.STATUS_COMPLETED:
            _audit(request, org_id=updated.org_id, action="project_completed", target_type="project", target_id=str(updated.id), metadata={}, property_id=updated.property_id, actor=request.user)
        if updated.status == Project.STATUS_CANCELLED:
            _audit(request, org_id=updated.org_id, action="project_cancelled", target_type="project", target_id=str(updated.id), metadata={}, property_id=updated.property_id, actor=request.user)
        if updated.status == Project.STATUS_VOID:
            _audit(request, org_id=updated.org_id, action="project_voided", target_type="project", target_id=str(updated.id), metadata={}, property_id=updated.property_id, actor=request.user)
        return Response(ProjectResponseSerializer(_project_dict(updated)).data)


class ProjectProgressUpdateView(APIView):
    lifecycle = ProjectLifecycleService()
    project_service = ProjectService()

    def post(self, request, project_id: int):
        if not _has_permission(request.user, "projects.manage"):
            return Response({"detail": "Permission required: projects.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProjectProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            project = self.project_service.get(project_id=project_id, org_id=data["org_id"])
            updated = self.lifecycle.update_progress(project=project, progress_percentage=data["progress_percentage"], actor=request.user, message=data.get("message", ""))
        except ProjectNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ProjectValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=updated.org_id, action="project_progress_updated", target_type="project", target_id=str(updated.id), metadata={"progress_percentage": updated.progress_percentage}, property_id=updated.property_id, actor=request.user)
        return Response(ProjectResponseSerializer(_project_dict(updated)).data)


class ProjectTimelineView(APIView):
    project_service = ProjectService()

    def get(self, request, project_id: int):
        if not _has_permission(request.user, "projects.view"):
            return Response({"detail": "Permission required: projects.view"}, status=status.HTTP_403_FORBIDDEN)
        try:
            project = self.project_service.get(project_id=project_id, org_id=int(request.query_params.get("org_id", "0")))
        except ProjectNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        rows = project.timeline_entries.order_by("-created_at")
        return Response({
            "count": rows.count(),
            "results": [
                {
                    "id": row.id,
                    "project_id": row.project_id,
                    "event_type": row.event_type,
                    "previous_status": row.previous_status,
                    "new_status": row.new_status,
                    "progress_percentage": row.progress_percentage,
                    "message": row.message,
                    "metadata": row.metadata_json,
                    "actor_id": row.actor_id,
                    "created_at": row.created_at,
                }
                for row in rows
            ]
        })


class SnaggingItemListCreateView(APIView):
    project_service = ProjectService()
    snag_service = SnaggingItemService()

    def post(self, request, project_id: int):
        if not _has_permission(request.user, "projects.manage"):
            return Response({"detail": "Permission required: projects.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = SnaggingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            project = self.project_service.get(project_id=project_id, org_id=data["org_id"])
            row = self.snag_service.create(project=project, actor=request.user, **{k: v for k, v in data.items() if k != "org_id"})
        except ProjectNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        _audit(request, org_id=project.org_id, action="snagging_item_created", target_type="snagging_item", target_id=str(row.id), metadata={"snag_number": row.snag_number}, property_id=project.property_id, actor=request.user)
        return Response(SnaggingResponseSerializer(_snag_dict(row)).data, status=status.HTTP_201_CREATED)

    def get(self, request, project_id: int):
        if not _has_permission(request.user, "projects.view"):
            return Response({"detail": "Permission required: projects.view"}, status=status.HTTP_403_FORBIDDEN)
        try:
            project = self.project_service.get(project_id=project_id, org_id=int(request.query_params.get("org_id", "0")))
        except ProjectNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        rows = self.snag_service.list_for_project(project_id=project.id)
        return Response({"count": rows.count(), "results": [SnaggingResponseSerializer(_snag_dict(x)).data for x in rows]})


class SnaggingItemDetailView(APIView):
    snag_service = SnaggingItemService()

    def get(self, request, snag_id: int):
        if not _has_permission(request.user, "projects.view"):
            return Response({"detail": "Permission required: projects.view"}, status=status.HTTP_403_FORBIDDEN)
        try:
            row = self.snag_service.get(snag_id=snag_id, org_id=int(request.query_params.get("org_id", "0")))
        except ProjectNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(SnaggingResponseSerializer(_snag_dict(row)).data)

    def patch(self, request, snag_id: int):
        if not _has_permission(request.user, "projects.manage"):
            return Response({"detail": "Permission required: projects.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = SnaggingUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            row = self.snag_service.get(snag_id=snag_id, org_id=int(request.data.get("org_id", "0")))
        except ProjectNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        for key in ["title", "description", "category", "severity", "location_id", "room_id", "asset_id", "due_at"]:
            if key in serializer.validated_data:
                setattr(row, key, serializer.validated_data[key])
        row.save()
        _audit(request, org_id=row.project.org_id, action="snagging_item_updated", target_type="snagging_item", target_id=str(row.id), metadata={"status": row.status}, property_id=row.project.property_id, actor=request.user)
        return Response(SnaggingResponseSerializer(_snag_dict(row)).data)


class SnaggingAssignView(APIView):
    snag_service = SnaggingItemService()

    def post(self, request, snag_id: int):
        if not _has_permission(request.user, "projects.manage"):
            return Response({"detail": "Permission required: projects.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = SnaggingAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            row = self.snag_service.get(snag_id=snag_id, org_id=data["org_id"])
        except ProjectNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        assignee = User.objects.filter(id=data["assignee_id"], org_id=data["org_id"]).first()
        if not assignee:
            return Response({"detail": "Assignee not found in organization"}, status=status.HTTP_400_BAD_REQUEST)
        row = self.snag_service.assign(snag=row, assignee=assignee, actor=request.user, reason=data.get("reason", ""))
        _audit(request, org_id=row.project.org_id, action="snagging_item_assigned", target_type="snagging_item", target_id=str(row.id), metadata={"assignee_id": assignee.id}, property_id=row.project.property_id, actor=request.user)
        return Response(SnaggingResponseSerializer(_snag_dict(row)).data)


class SnaggingTransitionView(APIView):
    snag_service = SnaggingItemService()
    target_status = ""

    def post(self, request, snag_id: int):
        if not _has_permission(request.user, "projects.manage"):
            return Response({"detail": "Permission required: projects.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = SnaggingTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            row = self.snag_service.get(snag_id=snag_id, org_id=data["org_id"])
            row = self.snag_service.transition(snag=row, to_status=self.target_status, actor=request.user, reason=data.get("reason", ""))
        except ProjectNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except (ProjectValidationError, SnaggingTransitionError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        action_map = {
            SnaggingItem.STATUS_IN_PROGRESS: "snagging_item_started",
            SnaggingItem.STATUS_RESOLVED: "snagging_item_resolved",
            SnaggingItem.STATUS_VERIFIED: "snagging_item_verified",
            SnaggingItem.STATUS_REOPENED: "snagging_item_reopened",
            SnaggingItem.STATUS_CANCELLED: "snagging_item_cancelled",
            SnaggingItem.STATUS_VOID: "snagging_item_voided",
        }
        action = action_map.get(self.target_status, "snagging_item_updated")
        _audit(request, org_id=row.project.org_id, action=action, target_type="snagging_item", target_id=str(row.id), metadata={"status": row.status}, property_id=row.project.property_id, actor=request.user)
        return Response(SnaggingResponseSerializer(_snag_dict(row)).data)


class SnaggingStartView(SnaggingTransitionView):
    target_status = SnaggingItem.STATUS_IN_PROGRESS


class SnaggingResolveView(SnaggingTransitionView):
    target_status = SnaggingItem.STATUS_RESOLVED


class SnaggingVerifyView(SnaggingTransitionView):
    target_status = SnaggingItem.STATUS_VERIFIED


class SnaggingReopenView(SnaggingTransitionView):
    target_status = SnaggingItem.STATUS_REOPENED


class SnaggingCancelView(SnaggingTransitionView):
    target_status = SnaggingItem.STATUS_CANCELLED


class SnaggingVoidView(SnaggingTransitionView):
    target_status = SnaggingItem.STATUS_VOID


class TechnicalAuditListCreateView(APIView):
    project_service = ProjectService()
    audit_service = TechnicalAuditService()

    def post(self, request, project_id: int):
        if not _has_permission(request.user, "projects.manage"):
            return Response({"detail": "Permission required: projects.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = TechnicalAuditCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            project = self.project_service.get(project_id=project_id, org_id=data["org_id"])
            row = self.audit_service.create(project=project, actor=request.user, **{k: v for k, v in data.items() if k != "org_id"})
        except (ProjectNotFoundError, ProjectValidationError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=project.org_id, action="technical_audit_created", target_type="technical_audit", target_id=str(row.id), metadata={"audit_number": row.audit_number}, property_id=project.property_id, actor=request.user)
        return Response(TechnicalAuditResponseSerializer(_audit_dict(row)).data, status=status.HTTP_201_CREATED)

    def get(self, request, project_id: int):
        if not _has_permission(request.user, "projects.view"):
            return Response({"detail": "Permission required: projects.view"}, status=status.HTTP_403_FORBIDDEN)
        try:
            project = self.project_service.get(project_id=project_id, org_id=int(request.query_params.get("org_id", "0")))
        except ProjectNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        rows = self.audit_service.list_for_project(project_id=project.id)
        return Response({"count": rows.count(), "results": [TechnicalAuditResponseSerializer(_audit_dict(x)).data for x in rows]})


class TechnicalAuditDetailView(APIView):
    audit_service = TechnicalAuditService()

    def get(self, request, audit_id: int):
        if not _has_permission(request.user, "projects.view"):
            return Response({"detail": "Permission required: projects.view"}, status=status.HTTP_403_FORBIDDEN)
        try:
            row = self.audit_service.get(audit_id=audit_id, org_id=int(request.query_params.get("org_id", "0")))
        except ProjectNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(TechnicalAuditResponseSerializer(_audit_dict(row)).data)

    def patch(self, request, audit_id: int):
        if not _has_permission(request.user, "projects.manage"):
            return Response({"detail": "Permission required: projects.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = TechnicalAuditUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            row = self.audit_service.get(audit_id=audit_id, org_id=int(request.data.get("org_id", "0")))
        except ProjectNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        for key in ["title", "scope", "auditor_id", "findings_summary", "corrective_actions_required", "conducted_at"]:
            if key in serializer.validated_data:
                setattr(row, key, serializer.validated_data[key])
        if "score" in serializer.validated_data:
            score = serializer.validated_data["score"]
            if score < 0 or score > 100:
                return Response({"detail": "score must be between 0 and 100"}, status=status.HTTP_400_BAD_REQUEST)
            row.score = score
        if "result" in serializer.validated_data:
            row.result = serializer.validated_data["result"]
        row.save()
        return Response(TechnicalAuditResponseSerializer(_audit_dict(row)).data)


class TechnicalAuditTransitionView(APIView):
    audit_service = TechnicalAuditService()
    target_status = ""

    def post(self, request, audit_id: int):
        if not _has_permission(request.user, "projects.manage"):
            return Response({"detail": "Permission required: projects.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = TechnicalAuditCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            row = self.audit_service.get(audit_id=audit_id, org_id=data["org_id"])
            row = self.audit_service.transition(
                audit=row,
                to_status=self.target_status,
                actor=request.user,
                result=data.get("result"),
                score=data.get("score"),
                findings_summary=data.get("findings_summary"),
                corrective_actions_required=data.get("corrective_actions_required"),
                auto_create_corrective_item=bool(data.get("auto_create_corrective_item", False)),
            )
        except ProjectNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except (ProjectValidationError, TechnicalAuditTransitionError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        action_map = {
            TechnicalAudit.STATUS_IN_PROGRESS: "technical_audit_started",
            TechnicalAudit.STATUS_COMPLETED: "technical_audit_completed",
            TechnicalAudit.STATUS_CANCELLED: "technical_audit_cancelled",
            TechnicalAudit.STATUS_VOID: "technical_audit_voided",
        }
        _audit(request, org_id=row.project.org_id, action=action_map.get(self.target_status, "technical_audit_updated"), target_type="technical_audit", target_id=str(row.id), metadata={"status": row.status}, property_id=row.project.property_id, actor=request.user)
        return Response(TechnicalAuditResponseSerializer(_audit_dict(row)).data)


class TechnicalAuditStartView(TechnicalAuditTransitionView):
    target_status = TechnicalAudit.STATUS_IN_PROGRESS


class TechnicalAuditCompleteView(TechnicalAuditTransitionView):
    target_status = TechnicalAudit.STATUS_COMPLETED


class TechnicalAuditCancelView(TechnicalAuditTransitionView):
    target_status = TechnicalAudit.STATUS_CANCELLED


class TechnicalAuditVoidView(TechnicalAuditTransitionView):
    target_status = TechnicalAudit.STATUS_VOID
