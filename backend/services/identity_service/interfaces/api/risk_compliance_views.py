from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.services.audit_logging import AuditContext
from application.services.risk_compliance import (
    AuditRecordRepository,
    ComplianceCheckFilters,
    ComplianceCheckRepository,
    ComplianceRequirementFilters,
    ComplianceRequirementRepository,
    ComplianceScheduleService,
    ComplianceStatusService,
    LegalRecordFilters,
    LegalRecordRepository,
    RiskComplianceAlertService,
    RiskComplianceDashboardService,
    RiskComplianceNotFoundError,
    RiskComplianceValidationError,
    RiskFilters,
    RiskMitigationService,
    RiskRepository,
    RiskScoringService,
    generate_risk_compliance_alerts,
    risk_compliance_audit_logs,
    update_legal_status,
)
from infrastructure.db.core.models import (
    AuditRecord,
    ComplianceCheck,
    ComplianceChecklistItem,
    ComplianceRequirement,
    LegalContractRecord,
    RiskMitigationAction,
    RiskRegisterItem,
    RolePermission,
    UserRole,
)
from infrastructure.services.audit_logging import get_audit_logger
from interfaces.api.serializers import (
    AuditRecordCreateSerializer,
    ComplianceCheckSubmitSerializer,
    ComplianceRequirementCreateSerializer,
    ComplianceRequirementUpdateSerializer,
    LegalRecordCreateSerializer,
    LegalRecordUpdateSerializer,
    MitigationCompleteSerializer,
    MitigationCreateSerializer,
    OrgOnlySerializer,
    RiskCreateSerializer,
    RiskUpdateSerializer,
)

MAX_PAGE_SIZE = 100


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


def _audit(request, *, org_id: int, action: str, entity_type: str, entity_id: str, metadata=None, property_id=None, actor=None):
    try:
        get_audit_logger().log_action(
            action=f"risk_compliance_{action}",
            target_type=entity_type,
            target_id=str(entity_id),
            metadata=metadata or {},
            context=_audit_context(request, org_id=org_id, property_id=property_id, actor=actor),
        )
    except Exception:
        pass


def _parse_page(request):
    page = max(int(request.query_params.get("page", "1") or "1"), 1)
    page_size = min(max(int(request.query_params.get("page_size", "10") or "10"), 1), MAX_PAGE_SIZE)
    return page, page_size


def _paginate_rows(qs, *, page: int, page_size: int):
    total = qs.count()
    offset = (page - 1) * page_size
    return total, qs[offset:offset + page_size]


def _req_dict(obj: ComplianceRequirement) -> dict:
    return {
        "id": obj.id,
        "requirement_code": obj.requirement_code,
        "title": obj.title,
        "description": obj.description,
        "category": obj.category,
        "regulation_reference": obj.regulation_reference,
        "property_id": obj.property_id,
        "department_id": obj.department_id,
        "owner_id": obj.owner_id,
        "frequency_type": obj.frequency_type,
        "frequency_interval": obj.frequency_interval,
        "priority": obj.priority,
        "status": obj.status,
        "effective_date": obj.effective_date,
        "expiry_date": obj.expiry_date,
        "next_run_at": obj.next_run_at,
        "created_by": obj.created_by_id,
        "updated_by": obj.updated_by_id,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
        "checklist_items": [
            {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "is_required": item.is_required,
                "sort_order": item.sort_order,
                "evidence_required": item.evidence_required,
            }
            for item in obj.checklist_items.order_by("sort_order", "id")
        ],
    }


def _check_dict(obj: ComplianceCheck) -> dict:
    return {
        "id": obj.id,
        "requirement_id": obj.requirement_id,
        "due_at": obj.due_at,
        "status": obj.status,
        "assigned_to": obj.assigned_to_id,
        "completed_by": obj.completed_by_id,
        "completed_at": obj.completed_at,
        "evidence_attachment_id": obj.evidence_attachment_id,
        "notes": obj.notes,
        "next_run_at": obj.next_run_at,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
    }


def _risk_dict(obj: RiskRegisterItem) -> dict:
    return {
        "id": obj.id,
        "risk_code": obj.risk_code,
        "title": obj.title,
        "description": obj.description,
        "category": obj.category,
        "property_id": obj.property_id,
        "department_id": obj.department_id,
        "owner_id": obj.owner_id,
        "likelihood": obj.likelihood,
        "impact": obj.impact,
        "inherent_score": obj.inherent_score,
        "residual_score": obj.residual_score,
        "risk_level": obj.risk_level,
        "status": obj.status,
        "identified_at": obj.identified_at,
        "reviewed_at": obj.reviewed_at,
        "due_at": obj.due_at,
        "created_by": obj.created_by_id,
        "updated_by": obj.updated_by_id,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
    }


def _legal_dict(obj: LegalContractRecord) -> dict:
    return {
        "id": obj.id,
        "record_code": obj.record_code,
        "title": obj.title,
        "description": obj.description,
        "record_type": obj.record_type,
        "property_id": obj.property_id,
        "department_id": obj.department_id,
        "owner_id": obj.owner_id,
        "vendor_name": obj.vendor_name,
        "effective_date": obj.effective_date,
        "expiry_date": obj.expiry_date,
        "renewal_due_at": obj.renewal_due_at,
        "status": obj.status,
        "attachment_id": obj.attachment_id,
        "notes": obj.notes,
        "created_by": obj.created_by_id,
        "updated_by": obj.updated_by_id,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
    }


def _audit_record_dict(obj: AuditRecord) -> dict:
    return {
        "id": obj.id,
        "audit_code": obj.audit_code,
        "title": obj.title,
        "scope": obj.scope,
        "auditor": obj.auditor,
        "property_id": obj.property_id,
        "department_id": obj.department_id,
        "audit_date": obj.audit_date,
        "result": obj.result,
        "score": obj.score,
        "findings_summary": obj.findings_summary,
        "corrective_actions_required": obj.corrective_actions_required,
        "attachment_id": obj.attachment_id,
        "related_risk_id": obj.related_risk_id,
        "related_check_id": obj.related_check_id,
        "created_by": obj.created_by_id,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
    }


class ComplianceRequirementListCreateView(APIView):
    repository = ComplianceRequirementRepository()

    @extend_schema(request=ComplianceRequirementCreateSerializer)
    @transaction.atomic
    def post(self, request):
        if not _has_permission(request.user, "risk_compliance.requirements.manage"):
            return Response({"detail": "Permission required: risk_compliance.requirements.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ComplianceRequirementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if ComplianceRequirement.objects.filter(requirement_code=data["requirement_code"]).exists():
            return Response({"detail": "requirement_code must be unique"}, status=status.HTTP_409_CONFLICT)
        req = self.repository.create(
            org_id=data["org_id"],
            requirement_code=data["requirement_code"],
            title=data["title"],
            description=data.get("description", ""),
            category=data.get("category", ""),
            regulation_reference=data.get("regulation_reference", ""),
            property_id=data.get("property_id"),
            department_id=data.get("department_id"),
            owner_id=data.get("owner_id"),
            frequency_type=data["frequency_type"],
            frequency_interval=data.get("frequency_interval", 1),
            priority=data.get("priority", ComplianceRequirement.PRIORITY_MEDIUM),
            status=data.get("status", ComplianceRequirement.STATUS_ACTIVE),
            effective_date=data.get("effective_date"),
            expiry_date=data.get("expiry_date"),
            next_run_at=timezone.now(),
            created_by=request.user,
            updated_by=request.user,
        )
        for item in data.get("checklist_items", []):
            ComplianceChecklistItem.objects.create(requirement=req, **item)
        _audit(request, org_id=req.org_id, action="compliance_requirement_created", entity_type="compliance_requirement", entity_id=str(req.id), actor=request.user)
        return Response(_req_dict(req), status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "risk_compliance.requirements.view"):
            return Response({"detail": "Permission required: risk_compliance.requirements.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        filters = ComplianceRequirementFilters(
            org_id=org_id,
            category=request.query_params.get("category"),
            property_id=int(request.query_params["property"]) if request.query_params.get("property") else None,
            department_id=int(request.query_params["department"]) if request.query_params.get("department") else None,
            owner_id=int(request.query_params["owner"]) if request.query_params.get("owner") else None,
            priority=request.query_params.get("priority"),
            status=request.query_params.get("status"),
        )
        qs = self.repository.list(filters)
        q = request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(requirement_code__icontains=q))
        page, page_size = _parse_page(request)
        total, rows = _paginate_rows(qs.order_by("-updated_at"), page=page, page_size=page_size)
        return Response({"count": total, "page": page, "page_size": page_size, "results": [_req_dict(r) for r in rows]})


class ComplianceRequirementDetailView(APIView):
    repository = ComplianceRequirementRepository()

    def get(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.requirements.view"):
            return Response({"detail": "Permission required: risk_compliance.requirements.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            req = self.repository.get_for_org(org_id=org_id, requirement_id=id)
        except RiskComplianceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(_req_dict(req), status=status.HTTP_200_OK)

    @transaction.atomic
    def patch(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.requirements.manage"):
            return Response({"detail": "Permission required: risk_compliance.requirements.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ComplianceRequirementUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        try:
            req = self.repository.get_for_org(org_id=org_id, requirement_id=id)
        except RiskComplianceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        for key, value in serializer.validated_data.items():
            if key == "checklist_items":
                continue
            setattr(req, key, value)
        req.updated_by = request.user
        req.save()
        if "checklist_items" in serializer.validated_data:
            ComplianceChecklistItem.objects.filter(requirement=req).delete()
            for item in serializer.validated_data["checklist_items"]:
                item.pop("id", None)
                ComplianceChecklistItem.objects.create(requirement=req, **item)
        _audit(request, org_id=req.org_id, action="compliance_requirement_updated", entity_type="compliance_requirement", entity_id=str(req.id), actor=request.user)
        return Response(_req_dict(req))


class ComplianceRequirementActivateView(APIView):
    def post(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.requirements.manage"):
            return Response({"detail": "Permission required: risk_compliance.requirements.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        req = ComplianceRequirement.objects.filter(org_id=org_id, id=id).first()
        if not req:
            return Response({"detail": "Compliance requirement not found"}, status=status.HTTP_404_NOT_FOUND)
        req.status = ComplianceRequirement.STATUS_ACTIVE
        req.save(update_fields=["status", "updated_at"])
        return Response(_req_dict(req))


class ComplianceRequirementDeactivateView(APIView):
    def post(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.requirements.manage"):
            return Response({"detail": "Permission required: risk_compliance.requirements.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        req = ComplianceRequirement.objects.filter(org_id=org_id, id=id).first()
        if not req:
            return Response({"detail": "Compliance requirement not found"}, status=status.HTTP_404_NOT_FOUND)
        req.status = ComplianceRequirement.STATUS_INACTIVE
        req.save(update_fields=["status", "updated_at"])
        return Response(_req_dict(req))


class ComplianceScheduleRunView(APIView):
    schedule_service = ComplianceScheduleService()

    def post(self, request):
        if not _has_permission(request.user, "risk_compliance.schedules.run"):
            return Response({"detail": "Permission required: risk_compliance.schedules.run"}, status=status.HTTP_403_FORBIDDEN)
        serializer = OrgOnlySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = self.schedule_service.run(org_id=serializer.validated_data["org_id"], actor=request.user)
        for _ in range(result.get("checks_created", 0)):
            _audit(request, org_id=serializer.validated_data["org_id"], action="compliance_check_generated", entity_type="compliance_check", entity_id="batch", actor=request.user)
        return Response(result, status=status.HTTP_200_OK)


class ComplianceCheckListView(APIView):
    repository = ComplianceCheckRepository()

    def get(self, request):
        if not _has_permission(request.user, "risk_compliance.checks.view"):
            return Response({"detail": "Permission required: risk_compliance.checks.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        filters = ComplianceCheckFilters(
            org_id=org_id,
            requirement_id=int(request.query_params["requirement_id"]) if request.query_params.get("requirement_id") else None,
            status=request.query_params.get("status"),
            property_id=int(request.query_params["property"]) if request.query_params.get("property") else None,
            department_id=int(request.query_params["department"]) if request.query_params.get("department") else None,
            owner_id=int(request.query_params["owner"]) if request.query_params.get("owner") else None,
            assigned_to=int(request.query_params["assigned_to"]) if request.query_params.get("assigned_to") else None,
            priority=request.query_params.get("priority"),
            category=request.query_params.get("category"),
        )
        page, page_size = _parse_page(request)
        total, rows = _paginate_rows(self.repository.list(filters).order_by("due_at"), page=page, page_size=page_size)
        return Response({"count": total, "page": page, "page_size": page_size, "results": [_check_dict(r) for r in rows]})


class ComplianceCheckDetailView(APIView):
    repository = ComplianceCheckRepository()

    def get(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.checks.view"):
            return Response({"detail": "Permission required: risk_compliance.checks.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            row = self.repository.get_for_org(org_id=org_id, check_id=id)
        except RiskComplianceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(_check_dict(row))


class ComplianceCheckSubmitView(APIView):
    repository = ComplianceCheckRepository()
    status_service = ComplianceStatusService()

    def post(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.checks.manage"):
            return Response({"detail": "Permission required: risk_compliance.checks.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ComplianceCheckSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            check = self.repository.get_for_org(org_id=data["org_id"], check_id=id)
            check.status = self.status_service.compute_check_status(check=check, compliant=data["compliant"], evidence_attachment_id=data.get("evidence_attachment_id"))
            check.evidence_attachment_id = data.get("evidence_attachment_id")
            check.notes = data.get("notes", "")
            check.completed_by = request.user
            check.completed_at = timezone.now()
            check.save()
        except RiskComplianceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except RiskComplianceValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=data["org_id"], action="compliance_check_submitted", entity_type="compliance_check", entity_id=str(check.id), actor=request.user)
        generate_risk_compliance_alerts(org_id=data["org_id"])
        return Response(_check_dict(check))


class ComplianceCheckWaiveView(APIView):
    repository = ComplianceCheckRepository()

    def post(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.checks.manage"):
            return Response({"detail": "Permission required: risk_compliance.checks.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = OrgOnlySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            check = self.repository.get_for_org(org_id=serializer.validated_data["org_id"], check_id=id)
        except RiskComplianceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        check.status = ComplianceCheck.STATUS_WAIVED
        check.completed_by = request.user
        check.completed_at = timezone.now()
        check.save()
        return Response(_check_dict(check))


class ComplianceCheckMarkOverdueView(APIView):
    status_service = ComplianceStatusService()

    def post(self, request):
        if not _has_permission(request.user, "risk_compliance.checks.manage"):
            return Response({"detail": "Permission required: risk_compliance.checks.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = OrgOnlySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        count = self.status_service.mark_overdue_checks(org_id=serializer.validated_data["org_id"])
        if count:
            _audit(request, org_id=serializer.validated_data["org_id"], action="compliance_check_marked_overdue", entity_type="compliance_check", entity_id="batch", actor=request.user, metadata={"count": count})
        generate_risk_compliance_alerts(org_id=serializer.validated_data["org_id"])
        return Response({"updated": count})


class RiskListCreateView(APIView):
    repository = RiskRepository()

    def post(self, request):
        if not _has_permission(request.user, "risk_compliance.risks.manage"):
            return Response({"detail": "Permission required: risk_compliance.risks.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = RiskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if RiskRegisterItem.objects.filter(risk_code=data["risk_code"]).exists():
            return Response({"detail": "risk_code must be unique"}, status=status.HTTP_409_CONFLICT)
        score = RiskScoringService.compute_score(likelihood=data["likelihood"], impact=data["impact"])
        risk = self.repository.create(
            org_id=data["org_id"],
            risk_code=data["risk_code"],
            title=data["title"],
            description=data.get("description", ""),
            category=data.get("category", ""),
            property_id=data.get("property_id"),
            department_id=data.get("department_id"),
            owner_id=data.get("owner_id"),
            likelihood=data["likelihood"],
            impact=data["impact"],
            inherent_score=score,
            residual_score=score,
            risk_level=RiskScoringService.risk_level(score),
            status=data.get("status", RiskRegisterItem.STATUS_OPEN),
            identified_at=data.get("identified_at", timezone.now()),
            reviewed_at=data.get("reviewed_at"),
            due_at=data.get("due_at"),
            created_by=request.user,
            updated_by=request.user,
        )
        _audit(request, org_id=risk.org_id, action="risk_created", entity_type="risk", entity_id=str(risk.id), actor=request.user)
        _audit(request, org_id=risk.org_id, action="risk_score_calculated", entity_type="risk", entity_id=str(risk.id), actor=request.user, metadata={"score": score, "level": risk.risk_level})
        generate_risk_compliance_alerts(org_id=risk.org_id)
        return Response(_risk_dict(risk), status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "risk_compliance.risks.view"):
            return Response({"detail": "Permission required: risk_compliance.risks.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        filters = RiskFilters(
            org_id=org_id,
            category=request.query_params.get("category"),
            property_id=int(request.query_params["property"]) if request.query_params.get("property") else None,
            department_id=int(request.query_params["department"]) if request.query_params.get("department") else None,
            owner_id=int(request.query_params["owner"]) if request.query_params.get("owner") else None,
            risk_level=request.query_params.get("risk_level"),
            status=request.query_params.get("status"),
        )
        q = request.query_params.get("q", "").strip()
        rows = self.repository.list(filters)
        if q:
            rows = rows.filter(Q(risk_code__icontains=q) | Q(title__icontains=q) | Q(category__icontains=q))
        if request.query_params.get("due_from"):
            due_from = parse_datetime(request.query_params["due_from"])
            if due_from:
                rows = rows.filter(due_at__gte=due_from)
        if request.query_params.get("due_to"):
            due_to = parse_datetime(request.query_params["due_to"])
            if due_to:
                rows = rows.filter(due_at__lte=due_to)
        page, page_size = _parse_page(request)
        total, rows = _paginate_rows(rows.order_by("-created_at"), page=page, page_size=page_size)
        return Response({"count": total, "page": page, "page_size": page_size, "results": [_risk_dict(r) for r in rows]})


class RiskDetailView(APIView):
    repository = RiskRepository()

    def get(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.risks.view"):
            return Response({"detail": "Permission required: risk_compliance.risks.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            row = self.repository.get_for_org(org_id=org_id, risk_id=id)
        except RiskComplianceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(_risk_dict(row))

    def patch(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.risks.manage"):
            return Response({"detail": "Permission required: risk_compliance.risks.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = RiskUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        try:
            row = self.repository.get_for_org(org_id=org_id, risk_id=id)
        except RiskComplianceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        if row.status in [RiskRegisterItem.STATUS_CLOSED, RiskRegisterItem.STATUS_VOID] and not _has_permission(request.user, "risk_compliance.risks.admin_override"):
            return Response({"detail": "Terminal risk cannot be modified without admin override"}, status=status.HTTP_400_BAD_REQUEST)
        for key, value in serializer.validated_data.items():
            setattr(row, key, value)
        if "likelihood" in serializer.validated_data or "impact" in serializer.validated_data:
            score = RiskScoringService.compute_score(likelihood=row.likelihood, impact=row.impact)
            row.inherent_score = score
            if not row.residual_score:
                row.residual_score = score
            row.risk_level = RiskScoringService.risk_level(score)
            _audit(request, org_id=row.org_id, action="risk_score_calculated", entity_type="risk", entity_id=str(row.id), actor=request.user, metadata={"score": score, "level": row.risk_level})
        row.updated_by = request.user
        row.save()
        _audit(request, org_id=row.org_id, action="risk_updated", entity_type="risk", entity_id=str(row.id), actor=request.user)
        return Response(_risk_dict(row))


class RiskMitigationListCreateView(APIView):
    mitigation_service = RiskMitigationService()

    def post(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.risks.manage"):
            return Response({"detail": "Permission required: risk_compliance.risks.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = MitigationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        risk = RiskRegisterItem.objects.filter(org_id=data["org_id"], id=id).first()
        if not risk:
            return Response({"detail": "Risk item not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            action = self.mitigation_service.create_action(
                risk=risk,
                title=data["title"],
                description=data.get("description", ""),
                assigned_to_id=data.get("assigned_to"),
                status=data.get("status", RiskMitigationAction.STATUS_PENDING),
                due_at=data.get("due_at"),
                effectiveness_score=data.get("effectiveness_score"),
                notes=data.get("notes", ""),
            )
        except RiskComplianceValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=data["org_id"], action="mitigation_action_created", entity_type="mitigation", entity_id=str(action.id), actor=request.user)
        return Response({"id": action.id, "risk_id": action.risk_id, "status": action.status}, status=status.HTTP_201_CREATED)

    def get(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.risks.view"):
            return Response({"detail": "Permission required: risk_compliance.risks.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        risk = RiskRegisterItem.objects.filter(org_id=org_id, id=id).first()
        if not risk:
            return Response({"detail": "Risk item not found"}, status=status.HTTP_404_NOT_FOUND)
        rows = risk.mitigation_actions.order_by("due_at", "id")
        return Response({"count": rows.count(), "results": [{"id": r.id, "title": r.title, "status": r.status, "due_at": r.due_at, "completed_at": r.completed_at, "effectiveness_score": r.effectiveness_score, "assigned_to": r.assigned_to_id} for r in rows]})


class RiskMitigationCompleteView(APIView):
    mitigation_service = RiskMitigationService()

    def post(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.risks.manage"):
            return Response({"detail": "Permission required: risk_compliance.risks.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = MitigationCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        action = RiskMitigationAction.objects.filter(id=id, risk__org_id=data["org_id"]).first()
        if not action:
            return Response({"detail": "Mitigation action not found"}, status=status.HTTP_404_NOT_FOUND)
        action, risk = self.mitigation_service.complete_action(action=action, effectiveness_score=data.get("effectiveness_score"), notes=data.get("notes", ""))
        _audit(request, org_id=data["org_id"], action="mitigation_action_completed", entity_type="mitigation", entity_id=str(action.id), actor=request.user)
        return Response({"mitigation_id": action.id, "status": action.status, "risk_residual_score": risk.residual_score, "risk_status": risk.status})


class LegalRecordListCreateView(APIView):
    repository = LegalRecordRepository()

    def post(self, request):
        if not _has_permission(request.user, "risk_compliance.legal.manage"):
            return Response({"detail": "Permission required: risk_compliance.legal.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = LegalRecordCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if LegalContractRecord.objects.filter(record_code=data["record_code"]).exists():
            return Response({"detail": "record_code must be unique"}, status=status.HTTP_409_CONFLICT)
        row = self.repository.create(created_by=request.user, updated_by=request.user, **data)
        row = update_legal_status(row)
        _audit(request, org_id=row.org_id, action="legal_record_created", entity_type="legal_record", entity_id=str(row.id), actor=request.user)
        generate_risk_compliance_alerts(org_id=row.org_id)
        return Response({"id": row.id, "record_code": row.record_code, "status": row.status}, status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "risk_compliance.legal.view"):
            return Response({"detail": "Permission required: risk_compliance.legal.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        from django.utils.dateparse import parse_date

        filters = LegalRecordFilters(
            org_id=org_id,
            record_type=request.query_params.get("type"),
            status=request.query_params.get("status"),
            property_id=int(request.query_params["property"]) if request.query_params.get("property") else None,
            department_id=int(request.query_params["department"]) if request.query_params.get("department") else None,
            owner_id=int(request.query_params["owner"]) if request.query_params.get("owner") else None,
            expiry_from=parse_date(request.query_params.get("expiry_from")) if request.query_params.get("expiry_from") else None,
            expiry_to=parse_date(request.query_params.get("expiry_to")) if request.query_params.get("expiry_to") else None,
        )
        rows = self.repository.list(filters)
        q = request.query_params.get("q", "").strip()
        if q:
            rows = rows.filter(Q(record_code__icontains=q) | Q(title__icontains=q) | Q(vendor_name__icontains=q))
        page, page_size = _parse_page(request)
        total, rows = _paginate_rows(rows.order_by("expiry_date", "id"), page=page, page_size=page_size)
        return Response({"count": total, "page": page, "page_size": page_size, "results": [_legal_dict(r) for r in rows]})


class LegalRecordDetailView(APIView):
    repository = LegalRecordRepository()

    def get(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.legal.view"):
            return Response({"detail": "Permission required: risk_compliance.legal.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            row = self.repository.get_for_org(org_id=org_id, record_id=id)
        except RiskComplianceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        row = update_legal_status(row)
        return Response(_legal_dict(row))

    def patch(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.legal.manage"):
            return Response({"detail": "Permission required: risk_compliance.legal.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = LegalRecordUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        try:
            row = self.repository.get_for_org(org_id=org_id, record_id=id)
        except RiskComplianceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        for key, value in serializer.validated_data.items():
            setattr(row, key, value)
        row.updated_by = request.user
        row.save()
        row = update_legal_status(row)
        _audit(request, org_id=row.org_id, action="legal_record_updated", entity_type="legal_record", entity_id=str(row.id), actor=request.user)
        return Response(_legal_dict(row))


class AuditRecordListCreateView(APIView):
    repository = AuditRecordRepository()

    def post(self, request):
        if not _has_permission(request.user, "risk_compliance.audit_records.manage"):
            return Response({"detail": "Permission required: risk_compliance.audit_records.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = AuditRecordCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if AuditRecord.objects.filter(audit_code=data["audit_code"]).exists():
            return Response({"detail": "audit_code must be unique"}, status=status.HTTP_409_CONFLICT)
        row = self.repository.create(
            org_id=data["org_id"],
            audit_code=data["audit_code"],
            title=data["title"],
            scope=data.get("scope", ""),
            auditor=data.get("auditor", ""),
            property_id=data.get("property_id"),
            department_id=data.get("department_id"),
            audit_date=data.get("audit_date"),
            result=data["result"],
            score=data.get("score"),
            findings_summary=data.get("findings_summary", ""),
            corrective_actions_required=data.get("corrective_actions_required", False),
            attachment_id=data.get("attachment_id"),
            related_risk_id=data.get("related_risk_id"),
            related_check_id=data.get("related_check_id"),
            created_by=request.user,
        )
        _audit(request, org_id=row.org_id, action="audit_record_created", entity_type="audit_record", entity_id=str(row.id), actor=request.user)
        generate_risk_compliance_alerts(org_id=row.org_id)
        return Response({"id": row.id, "audit_code": row.audit_code}, status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "risk_compliance.audit_records.view"):
            return Response({"detail": "Permission required: risk_compliance.audit_records.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        page, page_size = _parse_page(request)
        total, rows = _paginate_rows(self.repository.list(org_id=org_id).order_by("-created_at"), page=page, page_size=page_size)
        return Response({"count": total, "page": page, "page_size": page_size, "results": [_audit_record_dict(r) for r in rows]})


class AuditRecordDetailView(APIView):
    repository = AuditRecordRepository()

    def get(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.audit_records.view"):
            return Response({"detail": "Permission required: risk_compliance.audit_records.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            row = self.repository.get_for_org(org_id=org_id, record_id=id)
        except RiskComplianceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(_audit_record_dict(row))


class DashboardSummaryView(APIView):
    service = RiskComplianceDashboardService()

    def get(self, request):
        if not _has_permission(request.user, "risk_compliance.dashboard.view"):
            return Response({"detail": "Permission required: risk_compliance.dashboard.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        payload = self.service.summary(org_id=org_id)
        _audit(request, org_id=org_id, action="compliance_dashboard_viewed", entity_type="dashboard", entity_id="summary", actor=request.user)
        return Response(payload)


class DashboardComplianceStatusView(APIView):
    service = RiskComplianceDashboardService()

    def get(self, request):
        org_id = int(request.query_params.get("org_id", "0"))
        return Response(self.service.compliance_status(org_id=org_id))


class DashboardRiskSummaryView(APIView):
    service = RiskComplianceDashboardService()

    def get(self, request):
        org_id = int(request.query_params.get("org_id", "0"))
        return Response(self.service.risk_summary(org_id=org_id))


class DashboardLegalExpiryView(APIView):
    service = RiskComplianceDashboardService()

    def get(self, request):
        org_id = int(request.query_params.get("org_id", "0"))
        within_days = int(request.query_params.get("within_days", "30"))
        return Response(self.service.legal_expiry(org_id=org_id, within_days=within_days))


class AlertListView(APIView):
    service = RiskComplianceAlertService()

    def get(self, request):
        if not _has_permission(request.user, "risk_compliance.alerts.view"):
            return Response({"detail": "Permission required: risk_compliance.alerts.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        generate_risk_compliance_alerts(org_id=org_id)
        rows = self.service.list(org_id=org_id).order_by("-created_at")
        return Response({"count": rows.count(), "results": [{"id": r.id, "alert_type": r.alert_type, "severity": r.severity, "entity_type": r.entity_type, "entity_id": r.entity_id, "message": r.message, "assigned_to": r.assigned_to_id, "status": r.status, "created_at": r.created_at, "acknowledged_at": r.acknowledged_at, "resolved_at": r.resolved_at} for r in rows]})


class AlertAcknowledgeView(APIView):
    service = RiskComplianceAlertService()

    def post(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.alerts.manage"):
            return Response({"detail": "Permission required: risk_compliance.alerts.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = OrgOnlySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            row = self.service.acknowledge(org_id=serializer.validated_data["org_id"], alert_id=id)
        except RiskComplianceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        _audit(request, org_id=row.org_id, action="risk_compliance_alert_acknowledged", entity_type="risk_compliance_alert", entity_id=str(row.id), actor=request.user)
        return Response({"id": row.id, "status": row.status})


class AlertResolveView(APIView):
    service = RiskComplianceAlertService()

    def post(self, request, id: int):
        if not _has_permission(request.user, "risk_compliance.alerts.manage"):
            return Response({"detail": "Permission required: risk_compliance.alerts.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = OrgOnlySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            row = self.service.resolve(org_id=serializer.validated_data["org_id"], alert_id=id)
        except RiskComplianceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        _audit(request, org_id=row.org_id, action="risk_compliance_alert_resolved", entity_type="risk_compliance_alert", entity_id=str(row.id), actor=request.user)
        return Response({"id": row.id, "status": row.status})


class RiskComplianceAuditLogView(APIView):
    def get(self, request):
        if not _has_permission(request.user, "audit.view"):
            return Response({"detail": "Permission required: audit.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        rows = risk_compliance_audit_logs(org_id=org_id)
        q = request.query_params.get("q", "").strip()
        if q:
            rows = rows.filter(Q(action__icontains=q) | Q(target_type__icontains=q) | Q(target_id__icontains=q))
        if request.query_params.get("actor_user_id"):
            rows = rows.filter(actor_user_id=int(request.query_params["actor_user_id"]))
        if request.query_params.get("action"):
            rows = rows.filter(action__icontains=request.query_params["action"])
        if request.query_params.get("target_type"):
            rows = rows.filter(target_type__icontains=request.query_params["target_type"])
        if request.query_params.get("target_id"):
            rows = rows.filter(target_id=request.query_params["target_id"])
        page, page_size = _parse_page(request)
        total, rows = _paginate_rows(rows.order_by("-created_at"), page=page, page_size=page_size)
        return Response({"count": total, "page": page, "page_size": page_size, "results": [{"id": r.id, "actor_user_id": r.actor_user_id, "action": r.action, "target_type": r.target_type, "target_id": r.target_id, "metadata": r.metadata_json, "ip_address": r.ip_address, "user_agent": r.user_agent, "created_at": r.created_at} for r in rows]})


class RiskComplianceApprovalTrailView(APIView):
    def get(self, request):
        if not _has_permission(request.user, "audit.view"):
            return Response({"detail": "Permission required: audit.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        entity_type = request.query_params.get("entity_type", "").strip()
        entity_id = request.query_params.get("entity_id", "").strip()
        if not org_id or not entity_type or not entity_id:
            return Response({"detail": "org_id, entity_type and entity_id are required"}, status=status.HTTP_400_BAD_REQUEST)
        rows = risk_compliance_audit_logs(org_id=org_id).filter(target_type=entity_type, target_id=entity_id)
        approval_rows = rows.filter(action__in=["risk_compliance_approval_submitted", "risk_compliance_approval_approved", "risk_compliance_approval_rejected"]).order_by("created_at")
        return Response({
            "count": approval_rows.count(),
            "results": [
                {
                    "approver": str(r.actor_user_id or "System"),
                    "decision": "APPROVED" if r.action.endswith("approved") else "REJECTED" if r.action.endswith("rejected") else "PENDING",
                    "timestamp": r.created_at,
                    "comment": r.metadata_json.get("comment", ""),
                    "status": "COMPLETED" if r.action.endswith(("approved", "rejected")) else "PENDING",
                }
                for r in approval_rows
            ],
        })

    def post(self, request):
        if not _has_permission(request.user, "risk_compliance.approvals.manage"):
            return Response({"detail": "Permission required: risk_compliance.approvals.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        entity_type = str(request.data.get("entity_type", "")).strip()
        entity_id = str(request.data.get("entity_id", "")).strip()
        decision = str(request.data.get("decision", "")).strip().upper()
        comment = str(request.data.get("comment", "")).strip()
        if not org_id or not entity_type or not entity_id or decision not in ["APPROVE", "REJECT"]:
            return Response({"detail": "org_id, entity_type, entity_id and decision(APPROVE|REJECT) are required"}, status=status.HTTP_400_BAD_REQUEST)
        _audit(
            request,
            org_id=org_id,
            action="approval_approved" if decision == "APPROVE" else "approval_rejected",
            entity_type=entity_type,
            entity_id=entity_id,
            metadata={"comment": comment, "decision": decision},
            actor=request.user,
        )
        return Response({"entity_type": entity_type, "entity_id": entity_id, "decision": decision, "comment": comment}, status=status.HTTP_200_OK)
