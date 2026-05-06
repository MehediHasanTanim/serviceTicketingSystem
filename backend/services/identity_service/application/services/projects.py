from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from infrastructure.db.core.models import (
    Project,
    ProjectTimeline,
    SnaggingItem,
    SnaggingItemAssignmentHistory,
    SnaggingItemStatusHistory,
    TechnicalAudit,
    User,
)


class ProjectError(Exception):
    pass


class ProjectValidationError(ProjectError):
    pass


class ProjectNotFoundError(ProjectError):
    pass


class ProjectTransitionError(ProjectError):
    pass


class SnaggingTransitionError(ProjectError):
    pass


class TechnicalAuditTransitionError(ProjectError):
    pass


class ProjectLifecycleValidator:
    ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        Project.STATUS_DRAFT: {Project.STATUS_PLANNED, Project.STATUS_CANCELLED, Project.STATUS_VOID},
        Project.STATUS_PLANNED: {Project.STATUS_IN_PROGRESS, Project.STATUS_ON_HOLD, Project.STATUS_CANCELLED, Project.STATUS_VOID},
        Project.STATUS_IN_PROGRESS: {Project.STATUS_ON_HOLD, Project.STATUS_COMPLETED, Project.STATUS_CANCELLED, Project.STATUS_VOID},
        Project.STATUS_ON_HOLD: {Project.STATUS_IN_PROGRESS, Project.STATUS_CANCELLED, Project.STATUS_VOID},
        Project.STATUS_COMPLETED: set(),
        Project.STATUS_CANCELLED: set(),
        Project.STATUS_VOID: set(),
    }

    def validate(self, from_status: str, to_status: str, *, admin_override: bool = False) -> None:
        if admin_override:
            return
        allowed = self.ALLOWED_TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            raise ProjectTransitionError(f"Invalid project transition from {from_status} to {to_status}")


class SnaggingLifecycleValidator:
    ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        SnaggingItem.STATUS_OPEN: {SnaggingItem.STATUS_ASSIGNED, SnaggingItem.STATUS_IN_PROGRESS, SnaggingItem.STATUS_CANCELLED, SnaggingItem.STATUS_VOID},
        SnaggingItem.STATUS_ASSIGNED: {SnaggingItem.STATUS_IN_PROGRESS, SnaggingItem.STATUS_RESOLVED, SnaggingItem.STATUS_CANCELLED, SnaggingItem.STATUS_VOID},
        SnaggingItem.STATUS_IN_PROGRESS: {SnaggingItem.STATUS_RESOLVED, SnaggingItem.STATUS_CANCELLED, SnaggingItem.STATUS_VOID},
        SnaggingItem.STATUS_RESOLVED: {SnaggingItem.STATUS_VERIFIED, SnaggingItem.STATUS_REOPENED},
        SnaggingItem.STATUS_REOPENED: {SnaggingItem.STATUS_ASSIGNED, SnaggingItem.STATUS_IN_PROGRESS, SnaggingItem.STATUS_VOID},
        SnaggingItem.STATUS_VERIFIED: set(),
        SnaggingItem.STATUS_CANCELLED: set(),
        SnaggingItem.STATUS_VOID: set(),
    }

    def validate(self, from_status: str, to_status: str) -> None:
        allowed = self.ALLOWED_TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            raise SnaggingTransitionError(f"Invalid snagging transition from {from_status} to {to_status}")


class TechnicalAuditLifecycleValidator:
    ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        TechnicalAudit.STATUS_SCHEDULED: {TechnicalAudit.STATUS_IN_PROGRESS, TechnicalAudit.STATUS_CANCELLED, TechnicalAudit.STATUS_VOID},
        TechnicalAudit.STATUS_IN_PROGRESS: {TechnicalAudit.STATUS_COMPLETED, TechnicalAudit.STATUS_CANCELLED, TechnicalAudit.STATUS_VOID},
        TechnicalAudit.STATUS_COMPLETED: set(),
        TechnicalAudit.STATUS_CANCELLED: set(),
        TechnicalAudit.STATUS_VOID: set(),
    }

    def validate(self, from_status: str, to_status: str) -> None:
        allowed = self.ALLOWED_TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            raise TechnicalAuditTransitionError(f"Invalid technical audit transition from {from_status} to {to_status}")


@dataclass
class ProjectFilters:
    org_id: int
    property_id: int | None = None
    department_id: int | None = None
    project_type: str | None = None
    status: str | None = None
    priority: str | None = None
    owner_id: int | None = None
    manager_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    q: str | None = None


class ProjectRepository:
    def create(self, **kwargs) -> Project:
        return Project.objects.create(**kwargs)

    def get_for_org(self, *, project_id: int, org_id: int) -> Project:
        try:
            return Project.objects.get(id=project_id, org_id=org_id, is_deleted=False)
        except Project.DoesNotExist as exc:
            raise ProjectNotFoundError("Project not found") from exc

    def list(self, filters: ProjectFilters) -> QuerySet[Project]:
        qs = Project.objects.filter(org_id=filters.org_id, is_deleted=False)
        if filters.property_id:
            qs = qs.filter(property_id=filters.property_id)
        if filters.department_id:
            qs = qs.filter(department_id=filters.department_id)
        if filters.project_type:
            qs = qs.filter(project_type=filters.project_type)
        if filters.status:
            qs = qs.filter(status=filters.status)
        if filters.priority:
            qs = qs.filter(priority=filters.priority)
        if filters.owner_id:
            qs = qs.filter(owner_id=filters.owner_id)
        if filters.manager_id:
            qs = qs.filter(manager_id=filters.manager_id)
        if filters.date_from:
            qs = qs.filter(created_at__date__gte=filters.date_from)
        if filters.date_to:
            qs = qs.filter(created_at__date__lte=filters.date_to)
        if filters.q:
            q = filters.q.strip()
            if q:
                qs = qs.filter(Q(project_code__icontains=q) | Q(title__icontains=q))
        return qs

    def save(self, project: Project, *, update_fields: list[str] | None = None) -> Project:
        project.save(update_fields=update_fields)
        return project

    def soft_delete(self, project: Project) -> None:
        project.is_deleted = True
        project.deleted_at = timezone.now()
        self.save(project, update_fields=["is_deleted", "deleted_at"])


class ProjectTimelineRepository:
    def create(self, **kwargs) -> ProjectTimeline:
        return ProjectTimeline.objects.create(**kwargs)

    def list_for_project(self, *, project_id: int):
        return ProjectTimeline.objects.filter(project_id=project_id).order_by("-created_at")


class SnaggingItemRepository:
    def create(self, **kwargs) -> SnaggingItem:
        return SnaggingItem.objects.create(**kwargs)

    def get_for_org(self, *, snag_id: int, org_id: int) -> SnaggingItem:
        try:
            return SnaggingItem.objects.select_related("project").get(id=snag_id, project__org_id=org_id)
        except SnaggingItem.DoesNotExist as exc:
            raise ProjectNotFoundError("Snagging item not found") from exc

    def list_for_project(self, *, project_id: int):
        return SnaggingItem.objects.filter(project_id=project_id).order_by("-created_at")

    def save(self, snag: SnaggingItem, *, update_fields: list[str] | None = None) -> SnaggingItem:
        snag.save(update_fields=update_fields)
        return snag


class SnaggingHistoryRepository:
    def create_status(self, **kwargs) -> SnaggingItemStatusHistory:
        return SnaggingItemStatusHistory.objects.create(**kwargs)

    def create_assignment(self, **kwargs) -> SnaggingItemAssignmentHistory:
        return SnaggingItemAssignmentHistory.objects.create(**kwargs)


class TechnicalAuditRepository:
    def create(self, **kwargs) -> TechnicalAudit:
        return TechnicalAudit.objects.create(**kwargs)

    def get_for_org(self, *, audit_id: int, org_id: int) -> TechnicalAudit:
        try:
            return TechnicalAudit.objects.select_related("project").get(id=audit_id, project__org_id=org_id)
        except TechnicalAudit.DoesNotExist as exc:
            raise ProjectNotFoundError("Technical audit not found") from exc

    def list_for_project(self, *, project_id: int):
        return TechnicalAudit.objects.filter(project_id=project_id).order_by("-created_at")

    def save(self, audit: TechnicalAudit, *, update_fields: list[str] | None = None) -> TechnicalAudit:
        audit.save(update_fields=update_fields)
        return audit


class ProjectTimelineService:
    def __init__(self, *, timeline_repo: ProjectTimelineRepository | None = None) -> None:
        self.timeline_repo = timeline_repo or ProjectTimelineRepository()

    def record(self, *, project: Project, event_type: str, actor: User, previous_status: str | None = None, new_status: str | None = None, progress_percentage: int | None = None, message: str = "", metadata: dict | None = None) -> ProjectTimeline:
        return self.timeline_repo.create(
            project=project,
            event_type=event_type,
            previous_status=previous_status,
            new_status=new_status,
            progress_percentage=progress_percentage,
            message=message,
            metadata_json=metadata or {},
            actor=actor,
        )


class ProjectService:
    def __init__(self, *, repository: ProjectRepository | None = None, timeline_service: ProjectTimelineService | None = None) -> None:
        self.repository = repository or ProjectRepository()
        self.timeline_service = timeline_service or ProjectTimelineService()

    def _code(self, project_id: int) -> str:
        return f"PRJ-{project_id:08d}"

    @transaction.atomic
    def create(self, *, org_id: int, actor: User, **payload) -> Project:
        progress = int(payload.get("progress_percentage", 0))
        if progress < 0 or progress > 100:
            raise ProjectValidationError("progress_percentage must be between 0 and 100")
        project = self.repository.create(
            org_id=org_id,
            project_code=payload.get("project_code") or f"TMP-{timezone.now().timestamp()}",
            title=payload["title"],
            description=payload.get("description", ""),
            property_id=payload.get("property_id"),
            department_id=payload.get("department_id"),
            project_type=payload.get("project_type", Project.TYPE_OTHER),
            priority=payload.get("priority", Project.PRIORITY_MEDIUM),
            status=payload.get("status", Project.STATUS_DRAFT),
            owner_id=payload.get("owner_id"),
            manager_id=payload.get("manager_id"),
            start_date=payload.get("start_date"),
            planned_end_date=payload.get("planned_end_date"),
            actual_end_date=payload.get("actual_end_date"),
            budget_amount=payload.get("budget_amount", Decimal("0.00")),
            actual_cost=payload.get("actual_cost", Decimal("0.00")),
            progress_percentage=progress,
            created_by=actor,
            updated_by=actor,
        )
        if project.project_code.startswith("TMP-"):
            project.project_code = self._code(project.id)
            self.repository.save(project, update_fields=["project_code"])
        self.timeline_service.record(project=project, event_type=ProjectTimeline.EVENT_PROJECT_CREATED, actor=actor, new_status=project.status, progress_percentage=project.progress_percentage)
        return project

    def list(self, *, filters: ProjectFilters):
        return self.repository.list(filters)

    def get(self, *, project_id: int, org_id: int):
        return self.repository.get_for_org(project_id=project_id, org_id=org_id)

    @transaction.atomic
    def update(self, *, project: Project, actor: User, **payload) -> Project:
        for key in [
            "title", "description", "property_id", "department_id", "project_type", "priority", "owner_id", "manager_id",
            "start_date", "planned_end_date", "actual_end_date", "budget_amount", "actual_cost",
        ]:
            if key in payload:
                setattr(project, key, payload[key])
        if "progress_percentage" in payload:
            progress = int(payload["progress_percentage"])
            if progress < 0 or progress > 100:
                raise ProjectValidationError("progress_percentage must be between 0 and 100")
            project.progress_percentage = progress
        project.updated_by = actor
        self.repository.save(project)
        self.timeline_service.record(project=project, event_type=ProjectTimeline.EVENT_PROJECT_UPDATED, actor=actor, new_status=project.status, progress_percentage=project.progress_percentage)
        return project

    @transaction.atomic
    def delete(self, *, project: Project):
        self.repository.soft_delete(project)


class ProjectLifecycleService:
    def __init__(self, *, project_repo: ProjectRepository | None = None, snag_repo: SnaggingItemRepository | None = None, validator: ProjectLifecycleValidator | None = None, timeline_service: ProjectTimelineService | None = None) -> None:
        self.project_repo = project_repo or ProjectRepository()
        self.snag_repo = snag_repo or SnaggingItemRepository()
        self.validator = validator or ProjectLifecycleValidator()
        self.timeline_service = timeline_service or ProjectTimelineService()

    def _has_blocking_critical_snags(self, project: Project) -> bool:
        return self.snag_repo.list_for_project(project_id=project.id).filter(
            severity=SnaggingItem.SEVERITY_CRITICAL,
        ).exclude(status__in=[SnaggingItem.STATUS_RESOLVED, SnaggingItem.STATUS_VERIFIED, SnaggingItem.STATUS_CANCELLED, SnaggingItem.STATUS_VOID]).exists()

    @transaction.atomic
    def change_status(self, *, project: Project, to_status: str, actor: User, message: str = "", admin_override: bool = False, actual_end_date=None) -> Project:
        from_status = project.status
        self.validator.validate(from_status, to_status, admin_override=admin_override)
        if to_status == Project.STATUS_COMPLETED:
            if not actual_end_date and not project.actual_end_date:
                raise ProjectValidationError("actual_end_date is required when completing project")
            if self._has_blocking_critical_snags(project):
                raise ProjectValidationError("Critical unresolved snagging items block project completion")
            project.actual_end_date = actual_end_date or project.actual_end_date
        project.status = to_status
        project.updated_by = actor
        self.project_repo.save(project)
        self.timeline_service.record(
            project=project,
            event_type=ProjectTimeline.EVENT_PROJECT_STATUS_CHANGED,
            actor=actor,
            previous_status=from_status,
            new_status=to_status,
            progress_percentage=project.progress_percentage,
            message=message,
        )
        return project

    @transaction.atomic
    def update_progress(self, *, project: Project, progress_percentage: int, actor: User, message: str = "") -> Project:
        if progress_percentage < 0 or progress_percentage > 100:
            raise ProjectValidationError("progress_percentage must be between 0 and 100")
        project.progress_percentage = progress_percentage
        project.updated_by = actor
        self.project_repo.save(project)
        self.timeline_service.record(
            project=project,
            event_type=ProjectTimeline.EVENT_PROJECT_PROGRESS_UPDATED,
            actor=actor,
            progress_percentage=progress_percentage,
            message=message,
            new_status=project.status,
        )
        return project


class SnaggingItemService:
    def __init__(self, *, snag_repo: SnaggingItemRepository | None = None, project_repo: ProjectRepository | None = None, history_repo: SnaggingHistoryRepository | None = None, lifecycle_validator: SnaggingLifecycleValidator | None = None, timeline_service: ProjectTimelineService | None = None) -> None:
        self.snag_repo = snag_repo or SnaggingItemRepository()
        self.project_repo = project_repo or ProjectRepository()
        self.history_repo = history_repo or SnaggingHistoryRepository()
        self.lifecycle_validator = lifecycle_validator or SnaggingLifecycleValidator()
        self.timeline_service = timeline_service or ProjectTimelineService()

    def _number(self, snag_id: int) -> str:
        return f"SNG-{snag_id:08d}"

    @transaction.atomic
    def create(self, *, project: Project, actor: User, **payload) -> SnaggingItem:
        snag = self.snag_repo.create(
            project=project,
            snag_number=payload.get("snag_number") or f"TMP-{timezone.now().timestamp()}",
            title=payload["title"],
            description=payload.get("description", ""),
            category=payload.get("category", SnaggingItem.CATEGORY_OTHER),
            severity=payload.get("severity", SnaggingItem.SEVERITY_MEDIUM),
            status=SnaggingItem.STATUS_OPEN,
            location_id=payload.get("location_id"),
            room_id=payload.get("room_id"),
            asset_id=payload.get("asset_id"),
            assigned_to_id=payload.get("assigned_to"),
            reported_by=actor,
            due_at=payload.get("due_at"),
        )
        if snag.snag_number.startswith("TMP-"):
            snag.snag_number = self._number(snag.id)
            self.snag_repo.save(snag, update_fields=["snag_number"])
        self.history_repo.create_status(
            snagging_item=snag,
            previous_status=snag.status,
            new_status=snag.status,
            changed_by=actor,
            reason="Initial status",
            metadata_json={},
        )
        self.timeline_service.record(project=project, event_type=ProjectTimeline.EVENT_SNAGGING_ITEM_CREATED, actor=actor, message=snag.snag_number)
        return snag

    def list_for_project(self, *, project_id: int):
        return self.snag_repo.list_for_project(project_id=project_id)

    def get(self, *, snag_id: int, org_id: int):
        return self.snag_repo.get_for_org(snag_id=snag_id, org_id=org_id)

    @transaction.atomic
    def assign(self, *, snag: SnaggingItem, assignee: User, actor: User, reason: str = "") -> SnaggingItem:
        previous = snag.assigned_to
        snag.assigned_to = assignee
        if snag.status == SnaggingItem.STATUS_OPEN:
            self.transition(snag=snag, to_status=SnaggingItem.STATUS_ASSIGNED, actor=actor, reason=reason or "Assigned")
        else:
            self.snag_repo.save(snag)
        self.history_repo.create_assignment(
            snagging_item=snag,
            previous_assignee=previous,
            new_assignee=assignee,
            changed_by=actor,
            reason=reason,
        )
        return snag

    @transaction.atomic
    def transition(self, *, snag: SnaggingItem, to_status: str, actor: User, reason: str = "") -> SnaggingItem:
        from_status = snag.status
        self.lifecycle_validator.validate(from_status, to_status)
        if to_status in {SnaggingItem.STATUS_CANCELLED, SnaggingItem.STATUS_VOID} and not reason:
            raise ProjectValidationError("reason is required for cancel/void")
        if to_status == SnaggingItem.STATUS_REOPENED and not reason:
            raise ProjectValidationError("reason is required for reopen")
        snag.status = to_status
        if to_status == SnaggingItem.STATUS_RESOLVED:
            snag.resolved_at = timezone.now()
        if to_status == SnaggingItem.STATUS_VERIFIED:
            snag.verified_at = timezone.now()
        self.snag_repo.save(snag)
        self.history_repo.create_status(
            snagging_item=snag,
            previous_status=from_status,
            new_status=to_status,
            changed_by=actor,
            reason=reason,
            metadata_json={},
        )
        event = {
            SnaggingItem.STATUS_RESOLVED: ProjectTimeline.EVENT_SNAGGING_ITEM_RESOLVED,
        }.get(to_status, ProjectTimeline.EVENT_PROJECT_UPDATED)
        self.timeline_service.record(project=snag.project, event_type=event, actor=actor, message=f"{snag.snag_number}: {to_status}")
        return snag


class TechnicalAuditService:
    def __init__(self, *, audit_repo: TechnicalAuditRepository | None = None, lifecycle_validator: TechnicalAuditLifecycleValidator | None = None, timeline_service: ProjectTimelineService | None = None, snag_service: SnaggingItemService | None = None) -> None:
        self.audit_repo = audit_repo or TechnicalAuditRepository()
        self.lifecycle_validator = lifecycle_validator or TechnicalAuditLifecycleValidator()
        self.timeline_service = timeline_service or ProjectTimelineService()
        self.snag_service = snag_service or SnaggingItemService()

    def _number(self, audit_id: int) -> str:
        return f"TA-{audit_id:08d}"

    @transaction.atomic
    def create(self, *, project: Project, actor: User, **payload) -> TechnicalAudit:
        score = payload.get("score")
        if score is not None and (score < 0 or score > 100):
            raise ProjectValidationError("score must be between 0 and 100")
        audit = self.audit_repo.create(
            project=project,
            audit_number=payload.get("audit_number") or f"TMP-{timezone.now().timestamp()}",
            title=payload["title"],
            scope=payload.get("scope", ""),
            auditor_id=payload.get("auditor_id"),
            status=TechnicalAudit.STATUS_SCHEDULED,
            result=payload.get("result"),
            score=payload.get("score"),
            findings_summary=payload.get("findings_summary", ""),
            corrective_actions_required=payload.get("corrective_actions_required", False),
            conducted_at=payload.get("conducted_at"),
            created_by=actor,
        )
        if audit.audit_number.startswith("TMP-"):
            audit.audit_number = self._number(audit.id)
            self.audit_repo.save(audit, update_fields=["audit_number"])
        self.timeline_service.record(project=project, event_type=ProjectTimeline.EVENT_TECHNICAL_AUDIT_CREATED, actor=actor, message=audit.audit_number)
        return audit

    def list_for_project(self, *, project_id: int):
        return self.audit_repo.list_for_project(project_id=project_id)

    def get(self, *, audit_id: int, org_id: int):
        return self.audit_repo.get_for_org(audit_id=audit_id, org_id=org_id)

    @transaction.atomic
    def transition(self, *, audit: TechnicalAudit, to_status: str, actor: User, result: str | None = None, score: int | None = None, findings_summary: str | None = None, corrective_actions_required: bool | None = None, auto_create_corrective_item: bool = False) -> TechnicalAudit:
        self.lifecycle_validator.validate(audit.status, to_status)
        audit.status = to_status
        if score is not None and (score < 0 or score > 100):
            raise ProjectValidationError("score must be between 0 and 100")
        if score is not None:
            audit.score = score
        if result is not None:
            audit.result = result
        if findings_summary is not None:
            audit.findings_summary = findings_summary
        if corrective_actions_required is not None:
            audit.corrective_actions_required = corrective_actions_required
        if to_status == TechnicalAudit.STATUS_IN_PROGRESS and not audit.conducted_at:
            audit.conducted_at = timezone.now()
        if to_status == TechnicalAudit.STATUS_COMPLETED:
            audit.completed_at = timezone.now()
            if not audit.completed_at:
                raise ProjectValidationError("completed_at is required when technical audit is completed")
        self.audit_repo.save(audit)
        event = ProjectTimeline.EVENT_TECHNICAL_AUDIT_COMPLETED if to_status == TechnicalAudit.STATUS_COMPLETED else ProjectTimeline.EVENT_PROJECT_UPDATED
        self.timeline_service.record(project=audit.project, event_type=event, actor=actor, message=f"{audit.audit_number}: {to_status}")
        if to_status == TechnicalAudit.STATUS_COMPLETED and auto_create_corrective_item and audit.result == TechnicalAudit.RESULT_FAIL:
            self.snag_service.create(
                project=audit.project,
                actor=actor,
                title=f"Corrective action from audit {audit.audit_number}",
                description=audit.findings_summary or "Generated from failed technical audit",
                category=SnaggingItem.CATEGORY_QUALITY,
                severity=SnaggingItem.SEVERITY_HIGH,
            )
        return audit
