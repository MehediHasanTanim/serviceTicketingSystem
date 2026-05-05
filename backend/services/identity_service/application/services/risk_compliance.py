from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from infrastructure.db.core.models import (
    AuditLog,
    AuditRecord,
    ComplianceCheck,
    ComplianceChecklistItem,
    ComplianceRequirement,
    Department,
    LegalContractRecord,
    Property,
    RiskComplianceAlert,
    RiskMitigationAction,
    RiskRegisterItem,
    User,
)


class RiskComplianceError(Exception):
    pass


class RiskComplianceValidationError(RiskComplianceError):
    pass


class RiskComplianceNotFoundError(RiskComplianceError):
    pass


@dataclass
class ComplianceRequirementFilters:
    org_id: int
    category: str | None = None
    property_id: int | None = None
    department_id: int | None = None
    owner_id: int | None = None
    priority: str | None = None
    status: str | None = None


@dataclass
class ComplianceCheckFilters:
    org_id: int
    requirement_id: int | None = None
    status: str | None = None
    property_id: int | None = None
    department_id: int | None = None
    owner_id: int | None = None
    assigned_to: int | None = None
    priority: str | None = None
    category: str | None = None
    due_from: datetime | None = None
    due_to: datetime | None = None


@dataclass
class RiskFilters:
    org_id: int
    category: str | None = None
    property_id: int | None = None
    department_id: int | None = None
    owner_id: int | None = None
    risk_level: str | None = None
    status: str | None = None


@dataclass
class LegalRecordFilters:
    org_id: int
    record_type: str | None = None
    status: str | None = None
    property_id: int | None = None
    department_id: int | None = None
    owner_id: int | None = None
    expiry_from: date | None = None
    expiry_to: date | None = None


class ComplianceRequirementRepository:
    def create(self, **kwargs) -> ComplianceRequirement:
        return ComplianceRequirement.objects.create(**kwargs)

    def get_for_org(self, *, org_id: int, requirement_id: int) -> ComplianceRequirement:
        obj = ComplianceRequirement.objects.filter(org_id=org_id, id=requirement_id).first()
        if not obj:
            raise RiskComplianceNotFoundError("Compliance requirement not found")
        return obj

    def list(self, filters: ComplianceRequirementFilters) -> QuerySet[ComplianceRequirement]:
        qs = ComplianceRequirement.objects.filter(org_id=filters.org_id)
        if filters.category:
            qs = qs.filter(category__iexact=filters.category)
        if filters.property_id:
            qs = qs.filter(property_id=filters.property_id)
        if filters.department_id:
            qs = qs.filter(department_id=filters.department_id)
        if filters.owner_id:
            qs = qs.filter(owner_id=filters.owner_id)
        if filters.priority:
            qs = qs.filter(priority=filters.priority)
        if filters.status:
            qs = qs.filter(status=filters.status)
        return qs


class ComplianceChecklistRepository:
    def list_for_requirement(self, *, requirement_id: int) -> QuerySet[ComplianceChecklistItem]:
        return ComplianceChecklistItem.objects.filter(requirement_id=requirement_id).order_by("sort_order", "id")


class ComplianceCheckRepository:
    ACTIVE_STATUSES = [
        ComplianceCheck.STATUS_PENDING,
        ComplianceCheck.STATUS_IN_PROGRESS,
        ComplianceCheck.STATUS_NON_COMPLIANT,
        ComplianceCheck.STATUS_OVERDUE,
    ]

    def create(self, **kwargs) -> ComplianceCheck:
        return ComplianceCheck.objects.create(**kwargs)

    def get_for_org(self, *, org_id: int, check_id: int) -> ComplianceCheck:
        obj = ComplianceCheck.objects.select_related("requirement").filter(requirement__org_id=org_id, id=check_id).first()
        if not obj:
            raise RiskComplianceNotFoundError("Compliance check not found")
        return obj

    def list(self, filters: ComplianceCheckFilters) -> QuerySet[ComplianceCheck]:
        qs = ComplianceCheck.objects.select_related("requirement").filter(requirement__org_id=filters.org_id)
        if filters.requirement_id:
            qs = qs.filter(requirement_id=filters.requirement_id)
        if filters.status:
            qs = qs.filter(status=filters.status)
        if filters.assigned_to:
            qs = qs.filter(assigned_to_id=filters.assigned_to)
        if filters.due_from:
            qs = qs.filter(due_at__gte=filters.due_from)
        if filters.due_to:
            qs = qs.filter(due_at__lte=filters.due_to)
        if filters.property_id:
            qs = qs.filter(requirement__property_id=filters.property_id)
        if filters.department_id:
            qs = qs.filter(requirement__department_id=filters.department_id)
        if filters.owner_id:
            qs = qs.filter(requirement__owner_id=filters.owner_id)
        if filters.priority:
            qs = qs.filter(requirement__priority=filters.priority)
        if filters.category:
            qs = qs.filter(requirement__category__iexact=filters.category)
        return qs

    def has_active_for_period(self, *, requirement_id: int, period_start: datetime, period_end: datetime) -> bool:
        return ComplianceCheck.objects.filter(
            requirement_id=requirement_id,
            due_at__gte=period_start,
            due_at__lt=period_end,
            status__in=self.ACTIVE_STATUSES,
        ).exists()


class ComplianceStatusService:
    def compute_check_status(self, *, check: ComplianceCheck, compliant: bool, evidence_attachment_id: int | None) -> str:
        items = list(ComplianceChecklistItem.objects.filter(requirement_id=check.requirement_id))
        evidence_required = any(item.evidence_required and item.is_required for item in items)
        if evidence_required and not evidence_attachment_id:
            raise RiskComplianceValidationError("Evidence attachment is required")
        return ComplianceCheck.STATUS_COMPLIANT if compliant else ComplianceCheck.STATUS_NON_COMPLIANT

    def mark_overdue_checks(self, *, org_id: int, now: datetime | None = None) -> int:
        current = now or timezone.now()
        updated = ComplianceCheck.objects.filter(
            requirement__org_id=org_id,
            status__in=[ComplianceCheck.STATUS_PENDING, ComplianceCheck.STATUS_IN_PROGRESS],
            due_at__lt=current,
        ).update(status=ComplianceCheck.STATUS_OVERDUE)
        return updated

    def compliance_rate(self, *, org_id: int) -> Decimal:
        done = ComplianceCheck.objects.filter(
            requirement__org_id=org_id,
            status__in=[ComplianceCheck.STATUS_COMPLIANT, ComplianceCheck.STATUS_NON_COMPLIANT],
        )
        total = done.count()
        if total == 0:
            return Decimal("0")
        compliant = done.filter(status=ComplianceCheck.STATUS_COMPLIANT).count()
        return (Decimal(compliant) / Decimal(total) * Decimal("100")).quantize(Decimal("0.01"))


class ComplianceScheduleService:
    def __init__(
        self,
        *,
        requirement_repository: ComplianceRequirementRepository | None = None,
        check_repository: ComplianceCheckRepository | None = None,
    ) -> None:
        self.requirement_repository = requirement_repository or ComplianceRequirementRepository()
        self.check_repository = check_repository or ComplianceCheckRepository()

    def _step(self, requirement: ComplianceRequirement) -> timedelta:
        interval = max(requirement.frequency_interval or 1, 1)
        if requirement.frequency_type == ComplianceRequirement.FREQ_DAILY:
            return timedelta(days=interval)
        if requirement.frequency_type == ComplianceRequirement.FREQ_WEEKLY:
            return timedelta(weeks=interval)
        if requirement.frequency_type == ComplianceRequirement.FREQ_MONTHLY:
            return timedelta(days=30 * interval)
        if requirement.frequency_type == ComplianceRequirement.FREQ_QUARTERLY:
            return timedelta(days=90 * interval)
        if requirement.frequency_type == ComplianceRequirement.FREQ_YEARLY:
            return timedelta(days=365 * interval)
        return timedelta(days=interval)

    @transaction.atomic
    def run(self, *, org_id: int, actor: User | None = None, now: datetime | None = None) -> dict:
        current = now or timezone.now()
        summary = {"requirements_processed": 0, "checks_created": 0, "skipped_duplicates": 0, "errors": 0}
        requirements = ComplianceRequirement.objects.filter(
            org_id=org_id,
            status=ComplianceRequirement.STATUS_ACTIVE,
            next_run_at__lte=current,
        )
        for requirement in requirements:
            summary["requirements_processed"] += 1
            try:
                if requirement.expiry_date and requirement.expiry_date < current.date():
                    requirement.status = ComplianceRequirement.STATUS_INACTIVE
                    requirement.save(update_fields=["status", "updated_at"])
                    continue
                period_start = requirement.next_run_at
                period_end = period_start + self._step(requirement)
                if self.check_repository.has_active_for_period(
                    requirement_id=requirement.id,
                    period_start=period_start,
                    period_end=period_end,
                ):
                    summary["skipped_duplicates"] += 1
                    requirement.next_run_at = period_end
                    requirement.save(update_fields=["next_run_at", "updated_at"])
                    continue
                self.check_repository.create(
                    requirement=requirement,
                    due_at=period_start,
                    status=ComplianceCheck.STATUS_PENDING,
                    assigned_to_id=requirement.owner_id,
                    next_run_at=period_end,
                )
                summary["checks_created"] += 1
                requirement.next_run_at = period_end
                requirement.save(update_fields=["next_run_at", "updated_at"])
            except Exception:
                summary["errors"] += 1
        return summary


class RiskRepository:
    def create(self, **kwargs) -> RiskRegisterItem:
        return RiskRegisterItem.objects.create(**kwargs)

    def get_for_org(self, *, org_id: int, risk_id: int) -> RiskRegisterItem:
        obj = RiskRegisterItem.objects.filter(org_id=org_id, id=risk_id).first()
        if not obj:
            raise RiskComplianceNotFoundError("Risk item not found")
        return obj

    def list(self, filters: RiskFilters) -> QuerySet[RiskRegisterItem]:
        qs = RiskRegisterItem.objects.filter(org_id=filters.org_id)
        if filters.category:
            qs = qs.filter(category__iexact=filters.category)
        if filters.property_id:
            qs = qs.filter(property_id=filters.property_id)
        if filters.department_id:
            qs = qs.filter(department_id=filters.department_id)
        if filters.owner_id:
            qs = qs.filter(owner_id=filters.owner_id)
        if filters.risk_level:
            qs = qs.filter(risk_level=filters.risk_level)
        if filters.status:
            qs = qs.filter(status=filters.status)
        return qs


class RiskScoringService:
    @staticmethod
    def compute_score(*, likelihood: int, impact: int) -> int:
        if likelihood < 1 or likelihood > 5 or impact < 1 or impact > 5:
            raise RiskComplianceValidationError("likelihood and impact must be in range 1..5")
        return likelihood * impact

    @staticmethod
    def risk_level(score: int) -> str:
        if score <= 4:
            return RiskRegisterItem.LEVEL_LOW
        if score <= 9:
            return RiskRegisterItem.LEVEL_MEDIUM
        if score <= 16:
            return RiskRegisterItem.LEVEL_HIGH
        return RiskRegisterItem.LEVEL_CRITICAL


class RiskMitigationService:
    TERMINAL_RISK_STATUSES = {RiskRegisterItem.STATUS_CLOSED, RiskRegisterItem.STATUS_VOID}

    @transaction.atomic
    def create_action(self, *, risk: RiskRegisterItem, **payload) -> RiskMitigationAction:
        if risk.status in self.TERMINAL_RISK_STATUSES:
            raise RiskComplianceValidationError("Closed/void risk cannot accept mitigation actions")
        return RiskMitigationAction.objects.create(risk=risk, **payload)

    @transaction.atomic
    def complete_action(self, *, action: RiskMitigationAction, effectiveness_score: int | None = None, notes: str = "") -> tuple[RiskMitigationAction, RiskRegisterItem]:
        action.status = RiskMitigationAction.STATUS_COMPLETED
        action.completed_at = timezone.now()
        if effectiveness_score is not None:
            action.effectiveness_score = effectiveness_score
        if notes:
            action.notes = notes
        action.save()

        risk = action.risk
        effectiveness = action.effectiveness_score or 0
        reduction = min(effectiveness, 100) / 100
        risk.residual_score = max(int(risk.inherent_score * (1 - reduction)), 0)
        risk.risk_level = RiskScoringService.risk_level(max(risk.residual_score, 1))
        if risk.status in [RiskRegisterItem.STATUS_OPEN, RiskRegisterItem.STATUS_MITIGATING]:
            has_open = RiskMitigationAction.objects.filter(risk=risk).exclude(status=RiskMitigationAction.STATUS_COMPLETED).exists()
            risk.status = RiskRegisterItem.STATUS_MITIGATING if has_open else RiskRegisterItem.STATUS_MONITORING
        risk.reviewed_at = timezone.now()
        risk.save()
        return action, risk

    def mark_overdue(self, *, org_id: int, now: datetime | None = None) -> int:
        current = now or timezone.now()
        return RiskMitigationAction.objects.filter(
            risk__org_id=org_id,
            status__in=[RiskMitigationAction.STATUS_PENDING, RiskMitigationAction.STATUS_IN_PROGRESS],
            due_at__lt=current,
        ).update(status=RiskMitigationAction.STATUS_OVERDUE)


class LegalRecordRepository:
    def create(self, **kwargs) -> LegalContractRecord:
        return LegalContractRecord.objects.create(**kwargs)

    def get_for_org(self, *, org_id: int, record_id: int) -> LegalContractRecord:
        obj = LegalContractRecord.objects.filter(org_id=org_id, id=record_id).first()
        if not obj:
            raise RiskComplianceNotFoundError("Legal record not found")
        return obj

    def list(self, filters: LegalRecordFilters) -> QuerySet[LegalContractRecord]:
        qs = LegalContractRecord.objects.filter(org_id=filters.org_id)
        if filters.record_type:
            qs = qs.filter(record_type=filters.record_type)
        if filters.status:
            qs = qs.filter(status=filters.status)
        if filters.property_id:
            qs = qs.filter(property_id=filters.property_id)
        if filters.department_id:
            qs = qs.filter(department_id=filters.department_id)
        if filters.owner_id:
            qs = qs.filter(owner_id=filters.owner_id)
        if filters.expiry_from:
            qs = qs.filter(expiry_date__gte=filters.expiry_from)
        if filters.expiry_to:
            qs = qs.filter(expiry_date__lte=filters.expiry_to)
        return qs


class AuditRecordRepository:
    def create(self, **kwargs) -> AuditRecord:
        return AuditRecord.objects.create(**kwargs)

    def get_for_org(self, *, org_id: int, record_id: int) -> AuditRecord:
        obj = AuditRecord.objects.filter(org_id=org_id, id=record_id).first()
        if not obj:
            raise RiskComplianceNotFoundError("Audit record not found")
        return obj

    def list(self, *, org_id: int) -> QuerySet[AuditRecord]:
        return AuditRecord.objects.filter(org_id=org_id)


class RiskComplianceAlertService:
    def create_alert(
        self,
        *,
        org_id: int,
        alert_type: str,
        severity: str,
        entity_type: str,
        entity_id: str,
        message: str,
        assigned_to_id: int | None = None,
    ) -> RiskComplianceAlert | None:
        exists = RiskComplianceAlert.objects.filter(
            org_id=org_id,
            alert_type=alert_type,
            entity_type=entity_type,
            entity_id=entity_id,
            status__in=[RiskComplianceAlert.STATUS_OPEN, RiskComplianceAlert.STATUS_ACKNOWLEDGED],
        ).exists()
        if exists:
            return None
        return RiskComplianceAlert.objects.create(
            org_id=org_id,
            alert_type=alert_type,
            severity=severity,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message,
            assigned_to_id=assigned_to_id,
        )

    def list(self, *, org_id: int) -> QuerySet[RiskComplianceAlert]:
        return RiskComplianceAlert.objects.filter(org_id=org_id)

    @transaction.atomic
    def acknowledge(self, *, org_id: int, alert_id: int) -> RiskComplianceAlert:
        alert = RiskComplianceAlert.objects.filter(org_id=org_id, id=alert_id).first()
        if not alert:
            raise RiskComplianceNotFoundError("Alert not found")
        alert.status = RiskComplianceAlert.STATUS_ACKNOWLEDGED
        alert.acknowledged_at = timezone.now()
        alert.save()
        return alert

    @transaction.atomic
    def resolve(self, *, org_id: int, alert_id: int) -> RiskComplianceAlert:
        alert = RiskComplianceAlert.objects.filter(org_id=org_id, id=alert_id).first()
        if not alert:
            raise RiskComplianceNotFoundError("Alert not found")
        alert.status = RiskComplianceAlert.STATUS_RESOLVED
        alert.resolved_at = timezone.now()
        alert.save()
        return alert


class RiskComplianceDashboardService:
    def summary(self, *, org_id: int) -> dict:
        total_requirements = ComplianceRequirement.objects.filter(org_id=org_id).count()
        compliant_checks = ComplianceCheck.objects.filter(requirement__org_id=org_id, status=ComplianceCheck.STATUS_COMPLIANT).count()
        non_compliant_checks = ComplianceCheck.objects.filter(requirement__org_id=org_id, status=ComplianceCheck.STATUS_NON_COMPLIANT).count()
        overdue_checks = ComplianceCheck.objects.filter(requirement__org_id=org_id, status=ComplianceCheck.STATUS_OVERDUE).count()
        total_finished = compliant_checks + non_compliant_checks
        compliance_rate = float((Decimal(compliant_checks) / Decimal(total_finished) * Decimal("100")).quantize(Decimal("0.01")) if total_finished else Decimal("0"))
        open_risks = RiskRegisterItem.objects.filter(org_id=org_id, status__in=[RiskRegisterItem.STATUS_OPEN, RiskRegisterItem.STATUS_MITIGATING, RiskRegisterItem.STATUS_MONITORING]).count()
        critical_risks = RiskRegisterItem.objects.filter(org_id=org_id, risk_level=RiskRegisterItem.LEVEL_CRITICAL).count()
        overdue_mitigations = RiskMitigationAction.objects.filter(risk__org_id=org_id, status=RiskMitigationAction.STATUS_OVERDUE).count()
        expiring_contracts_count = LegalContractRecord.objects.filter(org_id=org_id, expiry_date__lte=(timezone.now().date() + timedelta(days=30))).exclude(status=LegalContractRecord.STATUS_ARCHIVED).count()
        audit_findings_count = AuditRecord.objects.filter(org_id=org_id, corrective_actions_required=True).count()
        return {
            "total_requirements": total_requirements,
            "compliant_checks": compliant_checks,
            "non_compliant_checks": non_compliant_checks,
            "overdue_checks": overdue_checks,
            "compliance_rate": compliance_rate,
            "open_risks": open_risks,
            "critical_risks": critical_risks,
            "overdue_mitigations": overdue_mitigations,
            "expiring_contracts_count": expiring_contracts_count,
            "audit_findings_count": audit_findings_count,
        }

    def compliance_status(self, *, org_id: int) -> dict:
        return {
            "compliant": ComplianceCheck.objects.filter(requirement__org_id=org_id, status=ComplianceCheck.STATUS_COMPLIANT).count(),
            "non_compliant": ComplianceCheck.objects.filter(requirement__org_id=org_id, status=ComplianceCheck.STATUS_NON_COMPLIANT).count(),
            "pending": ComplianceCheck.objects.filter(requirement__org_id=org_id, status=ComplianceCheck.STATUS_PENDING).count(),
            "overdue": ComplianceCheck.objects.filter(requirement__org_id=org_id, status=ComplianceCheck.STATUS_OVERDUE).count(),
        }

    def risk_summary(self, *, org_id: int) -> dict:
        levels = RiskRegisterItem.objects.filter(org_id=org_id).values("risk_level").annotate(count=Count("id"))
        payload = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for row in levels:
            payload[row["risk_level"]] = row["count"]
        payload["open"] = RiskRegisterItem.objects.filter(org_id=org_id, status=RiskRegisterItem.STATUS_OPEN).count()
        return payload

    def legal_expiry(self, *, org_id: int, within_days: int = 30) -> dict:
        until = timezone.now().date() + timedelta(days=within_days)
        return {
            "expiring_count": LegalContractRecord.objects.filter(org_id=org_id, expiry_date__lte=until, status=LegalContractRecord.STATUS_ACTIVE).count(),
            "expired_count": LegalContractRecord.objects.filter(org_id=org_id, expiry_date__lt=timezone.now().date()).count(),
        }


def update_legal_status(record: LegalContractRecord) -> LegalContractRecord:
    today = timezone.now().date()
    if record.status in [LegalContractRecord.STATUS_ARCHIVED, LegalContractRecord.STATUS_VOID]:
        return record
    if record.expiry_date and record.expiry_date < today:
        record.status = LegalContractRecord.STATUS_EXPIRED
    elif record.renewal_due_at and record.renewal_due_at <= timezone.now():
        record.status = LegalContractRecord.STATUS_RENEWAL_DUE
    else:
        record.status = LegalContractRecord.STATUS_ACTIVE
    record.save(update_fields=["status", "updated_at"])
    return record


def generate_risk_compliance_alerts(*, org_id: int, now: datetime | None = None) -> list[RiskComplianceAlert]:
    current = now or timezone.now()
    svc = RiskComplianceAlertService()
    created: list[RiskComplianceAlert] = []

    for check in ComplianceCheck.objects.filter(requirement__org_id=org_id, status=ComplianceCheck.STATUS_OVERDUE):
        alert = svc.create_alert(
            org_id=org_id,
            alert_type=RiskComplianceAlert.TYPE_COMPLIANCE_OVERDUE,
            severity=RiskComplianceAlert.SEVERITY_HIGH,
            entity_type="compliance_check",
            entity_id=str(check.id),
            message=f"Compliance check {check.id} is overdue",
            assigned_to_id=check.assigned_to_id,
        )
        if alert:
            created.append(alert)

    for check in ComplianceCheck.objects.filter(requirement__org_id=org_id, status=ComplianceCheck.STATUS_NON_COMPLIANT):
        alert = svc.create_alert(
            org_id=org_id,
            alert_type=RiskComplianceAlert.TYPE_NON_COMPLIANT,
            severity=RiskComplianceAlert.SEVERITY_HIGH,
            entity_type="compliance_check",
            entity_id=str(check.id),
            message=f"Compliance check {check.id} submitted as non-compliant",
            assigned_to_id=check.assigned_to_id,
        )
        if alert:
            created.append(alert)

    for risk in RiskRegisterItem.objects.filter(org_id=org_id, risk_level=RiskRegisterItem.LEVEL_CRITICAL):
        alert = svc.create_alert(
            org_id=org_id,
            alert_type=RiskComplianceAlert.TYPE_CRITICAL_RISK,
            severity=RiskComplianceAlert.SEVERITY_CRITICAL,
            entity_type="risk",
            entity_id=str(risk.id),
            message=f"Critical risk created: {risk.risk_code}",
            assigned_to_id=risk.owner_id,
        )
        if alert:
            created.append(alert)

    for action in RiskMitigationAction.objects.filter(risk__org_id=org_id, status=RiskMitigationAction.STATUS_OVERDUE):
        alert = svc.create_alert(
            org_id=org_id,
            alert_type=RiskComplianceAlert.TYPE_MITIGATION_OVERDUE,
            severity=RiskComplianceAlert.SEVERITY_HIGH,
            entity_type="mitigation",
            entity_id=str(action.id),
            message=f"Mitigation action {action.id} is overdue",
            assigned_to_id=action.assigned_to_id,
        )
        if alert:
            created.append(alert)

    threshold = current.date() + timedelta(days=30)
    for record in LegalContractRecord.objects.filter(org_id=org_id).exclude(status__in=[LegalContractRecord.STATUS_ARCHIVED, LegalContractRecord.STATUS_VOID]):
        if record.expiry_date and record.expiry_date <= threshold:
            alert = svc.create_alert(
                org_id=org_id,
                alert_type=RiskComplianceAlert.TYPE_LEGAL_EXPIRY,
                severity=RiskComplianceAlert.SEVERITY_MEDIUM,
                entity_type="legal_record",
                entity_id=str(record.id),
                message=f"{record.record_type} record {record.record_code} is nearing expiry",
                assigned_to_id=record.owner_id,
            )
            if alert:
                created.append(alert)

    for rec in AuditRecord.objects.filter(org_id=org_id, corrective_actions_required=True):
        alert = svc.create_alert(
            org_id=org_id,
            alert_type=RiskComplianceAlert.TYPE_AUDIT_CORRECTIVE,
            severity=RiskComplianceAlert.SEVERITY_HIGH,
            entity_type="audit_record",
            entity_id=str(rec.id),
            message=f"Audit {rec.audit_code} requires corrective action",
            assigned_to_id=None,
        )
        if alert:
            created.append(alert)

    return created


def risk_compliance_audit_logs(*, org_id: int) -> QuerySet[AuditLog]:
    return AuditLog.objects.filter(org_id=org_id, action__startswith="risk_compliance_").order_by("-created_at")
