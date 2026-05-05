from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q, QuerySet
from django.utils import timezone

from infrastructure.db.core.models import (
    Department,
    GuestComplaint,
    GuestComplaintEscalation,
    GuestComplaintFollowUp,
    GuestComplaintRoutingRule,
    GuestComplaintStatusHistory,
    User,
)


class GuestComplaintError(Exception):
    pass


class GuestComplaintValidationError(GuestComplaintError):
    pass


class GuestComplaintNotFoundError(GuestComplaintError):
    pass


class GuestComplaintTransitionError(GuestComplaintError):
    pass


class ComplaintLifecycleValidator:
    ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        GuestComplaint.STATUS_NEW: {GuestComplaint.STATUS_TRIAGED, GuestComplaint.STATUS_ASSIGNED, GuestComplaint.STATUS_VOID},
        GuestComplaint.STATUS_TRIAGED: {GuestComplaint.STATUS_ASSIGNED, GuestComplaint.STATUS_ESCALATED, GuestComplaint.STATUS_VOID},
        GuestComplaint.STATUS_ASSIGNED: {
            GuestComplaint.STATUS_IN_PROGRESS,
            GuestComplaint.STATUS_ESCALATED,
            GuestComplaint.STATUS_RESOLVED,
            GuestComplaint.STATUS_VOID,
        },
        GuestComplaint.STATUS_IN_PROGRESS: {GuestComplaint.STATUS_ESCALATED, GuestComplaint.STATUS_RESOLVED, GuestComplaint.STATUS_VOID},
        GuestComplaint.STATUS_ESCALATED: {GuestComplaint.STATUS_IN_PROGRESS, GuestComplaint.STATUS_RESOLVED, GuestComplaint.STATUS_VOID},
        GuestComplaint.STATUS_RESOLVED: {GuestComplaint.STATUS_CONFIRMED, GuestComplaint.STATUS_REOPENED},
        GuestComplaint.STATUS_CONFIRMED: {GuestComplaint.STATUS_CLOSED},
        GuestComplaint.STATUS_REOPENED: {
            GuestComplaint.STATUS_ASSIGNED,
            GuestComplaint.STATUS_IN_PROGRESS,
            GuestComplaint.STATUS_ESCALATED,
            GuestComplaint.STATUS_VOID,
        },
        GuestComplaint.STATUS_CLOSED: set(),
        GuestComplaint.STATUS_VOID: set(),
    }

    def validate(self, from_status: str, to_status: str, *, reason: str = "") -> None:
        allowed = self.ALLOWED_TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            raise GuestComplaintTransitionError(f"Invalid transition from {from_status} to {to_status}")
        if to_status == GuestComplaint.STATUS_REOPENED and not reason.strip():
            raise GuestComplaintTransitionError("Reopen requires reason")
        if to_status == GuestComplaint.STATUS_VOID and not reason.strip():
            raise GuestComplaintTransitionError("Void requires reason")


@dataclass
class ComplaintFilters:
    org_id: int
    status: str | None = None
    severity: str | None = None
    category: str | None = None
    source: str | None = None
    property_id: int | None = None
    department_id: int | None = None
    assigned_to: int | None = None
    escalated_to: int | None = None
    date_from: date | None = None
    date_to: date | None = None


class ComplaintRepository:
    def create(self, **kwargs) -> GuestComplaint:
        return GuestComplaint.objects.create(**kwargs)

    def get_for_org(self, *, complaint_id: int, org_id: int) -> GuestComplaint:
        try:
            return GuestComplaint.objects.get(id=complaint_id, org_id=org_id, is_deleted=False)
        except GuestComplaint.DoesNotExist as exc:
            raise GuestComplaintNotFoundError("Complaint not found") from exc

    def list(self, filters: ComplaintFilters) -> QuerySet[GuestComplaint]:
        qs = GuestComplaint.objects.filter(org_id=filters.org_id, is_deleted=False)
        if filters.status:
            qs = qs.filter(status=filters.status)
        if filters.severity:
            qs = qs.filter(severity=filters.severity)
        if filters.category:
            qs = qs.filter(category=filters.category)
        if filters.source:
            qs = qs.filter(source=filters.source)
        if filters.property_id:
            qs = qs.filter(property_id=filters.property_id)
        if filters.department_id:
            qs = qs.filter(department_id=filters.department_id)
        if filters.assigned_to:
            qs = qs.filter(assigned_to_id=filters.assigned_to)
        if filters.escalated_to:
            qs = qs.filter(escalated_to_id=filters.escalated_to)
        if filters.date_from:
            qs = qs.filter(created_at__date__gte=filters.date_from)
        if filters.date_to:
            qs = qs.filter(created_at__date__lte=filters.date_to)
        return qs

    def save(self, complaint: GuestComplaint, *, update_fields: list[str] | None = None) -> GuestComplaint:
        complaint.save(update_fields=update_fields)
        return complaint

    def soft_delete(self, complaint: GuestComplaint) -> None:
        complaint.is_deleted = True
        complaint.deleted_at = timezone.now()
        complaint.save(update_fields=["is_deleted", "deleted_at"])


class ComplaintStatusHistoryRepository:
    def create(self, **kwargs) -> GuestComplaintStatusHistory:
        return GuestComplaintStatusHistory.objects.create(**kwargs)


class ComplaintEscalationRepository:
    def create(self, **kwargs) -> GuestComplaintEscalation:
        return GuestComplaintEscalation.objects.create(**kwargs)

    def has_active(self, *, complaint: GuestComplaint, escalation_level: int) -> bool:
        return GuestComplaintEscalation.objects.filter(
            complaint=complaint,
            escalation_level=escalation_level,
            is_active=True,
        ).exists()


class ComplaintFollowUpRepository:
    def create(self, **kwargs) -> GuestComplaintFollowUp:
        return GuestComplaintFollowUp.objects.create(**kwargs)

    def list(self, *, complaint_id: int, assigned_to: int | None = None, status: str | None = None, date_from=None, date_to=None):
        qs = GuestComplaintFollowUp.objects.filter(complaint_id=complaint_id)
        if assigned_to:
            qs = qs.filter(assigned_to_id=assigned_to)
        if status:
            qs = qs.filter(status=status)
        if date_from:
            qs = qs.filter(scheduled_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(scheduled_at__date__lte=date_to)
        return qs


class ComplaintRoutingService:
    CATEGORY_DEPARTMENT_KEYWORDS = {
        GuestComplaint.CATEGORY_ROOM_CLEANLINESS: ["housekeeping"],
        GuestComplaint.CATEGORY_MAINTENANCE: ["maintenance"],
        GuestComplaint.CATEGORY_FOOD_BEVERAGE: ["f&b", "food", "beverage"],
        GuestComplaint.CATEGORY_BILLING: ["front office", "finance"],
        GuestComplaint.CATEGORY_SAFETY_SECURITY: ["security"],
        GuestComplaint.CATEGORY_STAFF_BEHAVIOR: ["guest relations", "hr"],
    }

    def _derive_shift(self, at: datetime | None) -> str:
        ref = at or timezone.now()
        hour = ref.hour
        if 6 <= hour < 14:
            return GuestComplaint.SHIFT_MORNING
        if 14 <= hour < 22:
            return GuestComplaint.SHIFT_AFTERNOON
        return GuestComplaint.SHIFT_NIGHT

    def route(self, *, complaint: GuestComplaint, vip_guest: bool = False) -> dict:
        if not complaint.shift:
            complaint.shift = self._derive_shift(complaint.reported_at)
            complaint.save(update_fields=["shift"])

        rule_qs = GuestComplaintRoutingRule.objects.filter(
            is_active=True,
            category=complaint.category,
        ).filter(
            Q(property_id=complaint.property_id) | Q(property_id__isnull=True)
        ).filter(
            Q(severity=complaint.severity) | Q(severity="")
        ).filter(
            Q(shift=complaint.shift) | Q(shift="")
        )
        if vip_guest:
            rule_qs = rule_qs.filter(Q(vip_only=True) | Q(vip_only=False))
        else:
            rule_qs = rule_qs.filter(vip_only=False)
        rule = rule_qs.order_by("priority", "id").first()

        selected = None
        if rule:
            selected = rule.department
            if rule.assign_to_id:
                complaint.assigned_to_id = rule.assign_to_id
                complaint.save(update_fields=["assigned_to"])
        else:
            terms = self.CATEGORY_DEPARTMENT_KEYWORDS.get(complaint.category, ["guest relations"])
            for term in terms:
                selected = Department.objects.filter(org_id=complaint.org_id, name__icontains=term).order_by("id").first()
                if selected:
                    break
            if not selected:
                selected = Department.objects.filter(org_id=complaint.org_id).order_by("id").first()
        metadata = {
            "category": complaint.category,
            "severity": complaint.severity,
            "vip_guest": vip_guest,
            "shift": complaint.shift,
            "rule_id": getattr(rule, "id", None),
            "selected_department_id": getattr(selected, "id", None),
            "fallback": rule is None,
        }
        if selected:
            complaint.department = selected
            complaint.save(update_fields=["department"])
        return metadata


class ComplaintLifecycleService:
    def __init__(
        self,
        *,
        repository: ComplaintRepository | None = None,
        history_repository: ComplaintStatusHistoryRepository | None = None,
        validator: ComplaintLifecycleValidator | None = None,
    ) -> None:
        self.repository = repository or ComplaintRepository()
        self.history_repository = history_repository or ComplaintStatusHistoryRepository()
        self.validator = validator or ComplaintLifecycleValidator()

    @transaction.atomic
    def transition(
        self,
        *,
        complaint: GuestComplaint,
        to_status: str,
        actor: User,
        reason: str = "",
        metadata: dict | None = None,
    ) -> GuestComplaint:
        from_status = complaint.status
        self.validator.validate(from_status, to_status, reason=reason)

        complaint.status = to_status
        complaint.updated_by = actor
        now = timezone.now()
        fields = ["status", "updated_by", "updated_at"]
        if to_status == GuestComplaint.STATUS_RESOLVED:
            complaint.resolved_at = now
            fields.append("resolved_at")
        if to_status == GuestComplaint.STATUS_CONFIRMED:
            complaint.confirmed_at = now
            fields.append("confirmed_at")
        self.repository.save(complaint, update_fields=fields)

        self.history_repository.create(
            complaint=complaint,
            previous_status=from_status,
            new_status=to_status,
            changed_by=actor,
            reason=reason,
            metadata_json=metadata or {},
        )
        return complaint


class ComplaintEscalationService:
    def __init__(
        self,
        *,
        escalation_repository: ComplaintEscalationRepository | None = None,
        lifecycle_service: ComplaintLifecycleService | None = None,
    ) -> None:
        self.escalation_repository = escalation_repository or ComplaintEscalationRepository()
        self.lifecycle_service = lifecycle_service or ComplaintLifecycleService()

    @transaction.atomic
    def escalate(
        self,
        *,
        complaint: GuestComplaint,
        actor: User | None,
        reason: str,
        escalated_to: User | None = None,
        escalation_level: int = 1,
        metadata: dict | None = None,
        manual: bool = False,
    ) -> tuple[bool, str]:
        if self.escalation_repository.has_active(complaint=complaint, escalation_level=escalation_level):
            return False, "duplicate_active_escalation"

        if complaint.status != GuestComplaint.STATUS_ESCALATED:
            try:
                self.lifecycle_service.transition(
                    complaint=complaint,
                    to_status=GuestComplaint.STATUS_ESCALATED,
                    actor=actor or complaint.updated_by,
                    reason=reason,
                    metadata={"trigger": "manual" if manual else "auto"},
                )
            except GuestComplaintTransitionError:
                return False, "invalid_transition"

        complaint.escalated_to = escalated_to
        complaint.updated_by = actor or complaint.updated_by
        complaint.save(update_fields=["escalated_to", "updated_by", "updated_at"])

        self.escalation_repository.create(
            complaint=complaint,
            escalation_level=escalation_level,
            escalated_from=actor,
            escalated_to=escalated_to,
            reason=reason,
            triggered_by=actor,
            metadata_json=metadata or {},
        )
        return True, "escalated"

    def run_batch(self, *, org_id: int, actor: User | None = None, now: datetime | None = None) -> dict:
        current = now or timezone.now()
        checked = 0
        escalated = 0
        skipped = 0
        errors = []
        qs = GuestComplaint.objects.filter(org_id=org_id, is_deleted=False).exclude(
            status__in=[GuestComplaint.STATUS_CLOSED, GuestComplaint.STATUS_VOID]
        )
        for complaint in qs:
            checked += 1
            try:
                should_escalate = False
                reason = ""
                if complaint.severity == GuestComplaint.SEVERITY_CRITICAL:
                    should_escalate = True
                    reason = "critical_severity"
                elif complaint.due_at and complaint.due_at < current:
                    should_escalate = True
                    reason = "overdue"
                elif complaint.status == GuestComplaint.STATUS_REOPENED:
                    should_escalate = True
                    reason = "reopened"

                if not should_escalate:
                    skipped += 1
                    continue

                done, flag = self.escalate(
                    complaint=complaint,
                    actor=actor,
                    reason=reason,
                    escalation_level=1,
                    metadata={"batch": True},
                )
                if done:
                    escalated += 1
                else:
                    skipped += 1
            except Exception as exc:  # pragma: no cover
                errors.append(str(exc))
        return {
            "checked_count": checked,
            "escalated_count": escalated,
            "skipped_count": skipped,
            "errors": errors,
        }


class ComplaintFollowUpService:
    def __init__(self, *, repository: ComplaintFollowUpRepository | None = None) -> None:
        self.repository = repository or ComplaintFollowUpRepository()

    def requires_auto_follow_up(self, *, complaint: GuestComplaint) -> bool:
        return complaint.severity in {GuestComplaint.SEVERITY_HIGH, GuestComplaint.SEVERITY_CRITICAL}

    @transaction.atomic
    def create_follow_up(
        self,
        *,
        complaint: GuestComplaint,
        follow_up_type: str,
        scheduled_at: datetime,
        created_by: User,
        assigned_to: User | None = None,
        notes: str = "",
    ) -> GuestComplaintFollowUp:
        return self.repository.create(
            complaint=complaint,
            follow_up_type=follow_up_type,
            scheduled_at=scheduled_at,
            created_by=created_by,
            assigned_to=assigned_to,
            notes=notes,
            status=GuestComplaintFollowUp.STATUS_PENDING,
        )

    @transaction.atomic
    def complete_follow_up(self, *, follow_up: GuestComplaintFollowUp, notes: str = "") -> GuestComplaintFollowUp:
        follow_up.status = GuestComplaintFollowUp.STATUS_COMPLETED
        follow_up.notes = notes or follow_up.notes
        follow_up.completed_at = timezone.now()
        follow_up.save(update_fields=["status", "notes", "completed_at", "updated_at"])
        return follow_up

    @transaction.atomic
    def mark_missed(self, *, now: datetime | None = None) -> int:
        current = now or timezone.now()
        updated = GuestComplaintFollowUp.objects.filter(
            status=GuestComplaintFollowUp.STATUS_PENDING,
            scheduled_at__lt=current,
        ).update(status=GuestComplaintFollowUp.STATUS_MISSED, updated_at=current)
        return updated


class ResolutionConfirmationService:
    def __init__(
        self,
        *,
        lifecycle_service: ComplaintLifecycleService | None = None,
        escalation_service: ComplaintEscalationService | None = None,
    ) -> None:
        self.lifecycle_service = lifecycle_service or ComplaintLifecycleService()
        self.escalation_service = escalation_service or ComplaintEscalationService()

    @transaction.atomic
    def confirm(
        self,
        *,
        complaint: GuestComplaint,
        actor: User,
        satisfaction_score: Decimal | float | int,
        satisfaction_comment: str = "",
        auto_reopen_low_score: bool = True,
        low_score_threshold: Decimal = Decimal("2.00"),
    ) -> GuestComplaint:
        if complaint.status != GuestComplaint.STATUS_RESOLVED:
            raise GuestComplaintValidationError("Complaint must be RESOLVED before confirmation")

        score = Decimal(str(satisfaction_score)).quantize(Decimal("0.01"))
        complaint.satisfaction_score = score
        complaint.satisfaction_comment = satisfaction_comment
        complaint.updated_by = actor
        complaint.save(update_fields=["satisfaction_score", "satisfaction_comment", "updated_by", "updated_at"])

        self.lifecycle_service.transition(
            complaint=complaint,
            to_status=GuestComplaint.STATUS_CONFIRMED,
            actor=actor,
            reason="resolution_confirmed",
            metadata={},
        )

        if auto_reopen_low_score and score <= low_score_threshold:
            self.lifecycle_service.transition(
                complaint=complaint,
                to_status=GuestComplaint.STATUS_REOPENED,
                actor=actor,
                reason="low_satisfaction",
            )
        return complaint


class GuestExperienceAnalyticsService:
    def _base_qs(self, *, org_id: int, filters: ComplaintFilters) -> QuerySet[GuestComplaint]:
        qs = GuestComplaint.objects.filter(org_id=org_id, is_deleted=False)
        if filters.property_id:
            qs = qs.filter(property_id=filters.property_id)
        if filters.department_id:
            qs = qs.filter(department_id=filters.department_id)
        if filters.category:
            qs = qs.filter(category=filters.category)
        if filters.severity:
            qs = qs.filter(severity=filters.severity)
        if filters.source:
            qs = qs.filter(source=filters.source)
        if filters.date_from:
            qs = qs.filter(created_at__date__gte=filters.date_from)
        if filters.date_to:
            qs = qs.filter(created_at__date__lte=filters.date_to)
        return qs

    def summary(self, *, org_id: int, filters: ComplaintFilters) -> dict:
        qs = self._base_qs(org_id=org_id, filters=filters)
        total = qs.count()
        resolved = qs.filter(status=GuestComplaint.STATUS_RESOLVED).count()
        return {
            "total_complaints": total,
            "open_complaints": qs.exclude(status__in=[GuestComplaint.STATUS_CLOSED, GuestComplaint.STATUS_VOID]).count(),
            "resolved_complaints": resolved,
            "escalated_complaints": qs.filter(status=GuestComplaint.STATUS_ESCALATED).count(),
            "reopened_complaints": qs.filter(status=GuestComplaint.STATUS_REOPENED).count(),
            "sla_compliance_percentage": float((resolved / total) * 100) if total else 0.0,
            "complaints_by_category": list(qs.values("category").annotate(count=Count("id")).order_by("category")),
            "complaints_by_severity": list(qs.values("severity").annotate(count=Count("id")).order_by("severity")),
        }

    def trends(self, *, org_id: int, filters: ComplaintFilters, group_by: str = "day") -> list[dict]:
        qs = self._base_qs(org_id=org_id, filters=filters)
        if group_by == "month":
            key = "created_at__month"
        elif group_by == "week":
            key = "created_at__week"
        else:
            key = "created_at__date"
        rows = qs.values(key).annotate(count=Count("id")).order_by(key)
        return [{"period": row[key], "count": row["count"]} for row in rows]

    def resolution_time(self, *, org_id: int, filters: ComplaintFilters) -> dict:
        qs = self._base_qs(org_id=org_id, filters=filters).filter(resolved_at__isnull=False)
        avg = qs.annotate(
            delta=ExpressionWrapper(F("resolved_at") - F("created_at"), output_field=DurationField())
        ).aggregate(avg_delta=Avg("delta"))["avg_delta"]
        avg_hours = (avg.total_seconds() / 3600.0) if avg else 0.0
        return {"average_resolution_time_hours": avg_hours, "resolved_count": qs.count()}

    def satisfaction(self, *, org_id: int, filters: ComplaintFilters) -> dict:
        qs = self._base_qs(org_id=org_id, filters=filters).filter(satisfaction_score__isnull=False)
        avg_score = qs.aggregate(avg=Avg("satisfaction_score"))["avg"] or Decimal("0.00")
        low = qs.filter(satisfaction_score__lte=Decimal("2.00")).count()
        return {
            "average_satisfaction_score": float(avg_score),
            "low_satisfaction_count": low,
            "responses_count": qs.count(),
        }


class ComplaintService:
    def __init__(
        self,
        *,
        repository: ComplaintRepository | None = None,
        lifecycle_service: ComplaintLifecycleService | None = None,
        routing_service: ComplaintRoutingService | None = None,
        escalation_service: ComplaintEscalationService | None = None,
        follow_up_service: ComplaintFollowUpService | None = None,
    ) -> None:
        self.repository = repository or ComplaintRepository()
        self.lifecycle_service = lifecycle_service or ComplaintLifecycleService(repository=self.repository)
        self.routing_service = routing_service or ComplaintRoutingService()
        self.escalation_service = escalation_service or ComplaintEscalationService(lifecycle_service=self.lifecycle_service)
        self.follow_up_service = follow_up_service or ComplaintFollowUpService()

    def _generate_number(self, complaint_id: int) -> str:
        return f"GC-{complaint_id:08d}"

    @transaction.atomic
    def create(self, *, created_by: User, org_id: int, **payload) -> tuple[GuestComplaint, dict]:
        complaint = self.repository.create(
            org_id=org_id,
            complaint_number=f"TEMP-{timezone.now().timestamp()}",
            guest_id=payload.get("guest_id"),
            guest_name=payload["guest_name"],
            guest_contact=payload.get("guest_contact", ""),
            property_id=payload["property_id"],
            room_id=payload.get("room_id"),
            department_id=payload.get("department_id"),
            category=payload["category"],
            severity=payload.get("severity", GuestComplaint.SEVERITY_MEDIUM),
            status=GuestComplaint.STATUS_NEW,
            title=payload["title"],
            description=payload.get("description", ""),
            source=payload.get("source", GuestComplaint.SOURCE_FRONT_DESK),
            vip_guest=bool(payload.get("vip_guest", False)),
            reported_at=payload.get("reported_at"),
            shift=payload.get("shift", ""),
            assigned_to=payload.get("assigned_to"),
            due_at=payload.get("due_at"),
            created_by=created_by,
            updated_by=created_by,
        )
        complaint.complaint_number = self._generate_number(complaint.id)
        complaint.save(update_fields=["complaint_number"])
        route_meta = self.routing_service.route(complaint=complaint, vip_guest=bool(payload.get("vip_guest", False)))
        if complaint.severity == GuestComplaint.SEVERITY_CRITICAL:
            self.escalation_service.escalate(
                complaint=complaint,
                actor=created_by,
                reason="critical_severity",
                metadata={"auto": True},
            )
        return complaint, route_meta

    def get(self, *, complaint_id: int, org_id: int) -> GuestComplaint:
        return self.repository.get_for_org(complaint_id=complaint_id, org_id=org_id)

    def list(self, *, filters: ComplaintFilters):
        return self.repository.list(filters)

    @transaction.atomic
    def update(self, *, complaint: GuestComplaint, actor: User, **payload) -> GuestComplaint:
        for key in ["guest_name", "guest_contact", "category", "severity", "title", "description", "source", "due_at", "vip_guest", "reported_at", "shift"]:
            if key in payload:
                setattr(complaint, key, payload[key])
        if "department_id" in payload:
            complaint.department_id = payload["department_id"]
        complaint.updated_by = actor
        complaint.save()
        return complaint

    @transaction.atomic
    def assign(self, *, complaint: GuestComplaint, assignee: User, actor: User, reason: str = "") -> GuestComplaint:
        complaint.assigned_to = assignee
        complaint.updated_by = actor
        complaint.save(update_fields=["assigned_to", "updated_by", "updated_at"])
        if complaint.status in {GuestComplaint.STATUS_NEW, GuestComplaint.STATUS_TRIAGED, GuestComplaint.STATUS_REOPENED}:
            self.lifecycle_service.transition(
                complaint=complaint,
                to_status=GuestComplaint.STATUS_ASSIGNED,
                actor=actor,
                reason=reason,
            )
        return complaint
