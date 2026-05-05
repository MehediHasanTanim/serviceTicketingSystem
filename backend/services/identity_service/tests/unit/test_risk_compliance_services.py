from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from application.services.risk_compliance import (
    ComplianceScheduleService,
    ComplianceStatusService,
    RiskComplianceAlertService,
    RiskComplianceDashboardService,
    RiskMitigationService,
    RiskScoringService,
    RiskComplianceValidationError,
    generate_risk_compliance_alerts,
    update_legal_status,
)
from infrastructure.db.core.models import (
    AuditLog,
    AuditRecord,
    ComplianceCheck,
    ComplianceChecklistItem,
    ComplianceRequirement,
    LegalContractRecord,
    RiskComplianceAlert,
    RiskMitigationAction,
    RiskRegisterItem,
)
from tests.unit.api_test_helpers import create_org, create_user


@pytest.mark.django_db
@pytest.mark.unit
def test_compliance_schedule_generation_duplicate_skip_inactive_skip_overdue_mark_rate():
    org = create_org("RC Org")
    actor = create_user(org, email="rc@example.com")

    active_req = ComplianceRequirement.objects.create(
        org=org,
        requirement_code="CR-001",
        title="Daily check",
        frequency_type=ComplianceRequirement.FREQ_DAILY,
        frequency_interval=1,
        status=ComplianceRequirement.STATUS_ACTIVE,
        next_run_at=timezone.now() - timedelta(minutes=5),
        created_by=actor,
        updated_by=actor,
    )
    ComplianceChecklistItem.objects.create(requirement=active_req, title="Photo", is_required=True, evidence_required=True)

    inactive_req = ComplianceRequirement.objects.create(
        org=org,
        requirement_code="CR-002",
        title="Inactive",
        frequency_type=ComplianceRequirement.FREQ_DAILY,
        frequency_interval=1,
        status=ComplianceRequirement.STATUS_INACTIVE,
        next_run_at=timezone.now() - timedelta(minutes=5),
        created_by=actor,
        updated_by=actor,
    )

    svc = ComplianceScheduleService()
    summary1 = svc.run(org_id=org.id, actor=actor)
    assert summary1["requirements_processed"] == 1
    assert summary1["checks_created"] == 1
    check = ComplianceCheck.objects.get(requirement=active_req)

    summary2 = svc.run(org_id=org.id, actor=actor, now=check.due_at + timedelta(hours=1))
    assert summary2["skipped_duplicates"] >= 1

    status_svc = ComplianceStatusService()
    with pytest.raises(RiskComplianceValidationError):
        status_svc.compute_check_status(check=check, compliant=False, evidence_attachment_id=None)

    check.due_at = timezone.now() - timedelta(days=2)
    check.status = ComplianceCheck.STATUS_PENDING
    check.save(update_fields=["due_at", "status", "updated_at"])
    updated = status_svc.mark_overdue_checks(org_id=org.id)
    assert updated >= 1
    check.refresh_from_db()
    assert check.status == ComplianceCheck.STATUS_OVERDUE

    check.status = ComplianceCheck.STATUS_COMPLIANT
    check.save(update_fields=["status", "updated_at"])
    ComplianceCheck.objects.create(requirement=active_req, due_at=timezone.now(), status=ComplianceCheck.STATUS_NON_COMPLIANT)
    assert status_svc.compliance_rate(org_id=org.id) == Decimal("50.00")
    assert ComplianceRequirement.objects.filter(id=inactive_req.id, status=ComplianceRequirement.STATUS_INACTIVE).exists()


@pytest.mark.django_db
@pytest.mark.unit
def test_risk_scoring_mitigation_terminal_behavior_and_alerts():
    org = create_org("Risk Org")
    actor = create_user(org, email="risk@example.com")

    assert RiskScoringService.compute_score(likelihood=2, impact=2) == 4
    assert RiskScoringService.risk_level(4) == RiskRegisterItem.LEVEL_LOW
    assert RiskScoringService.risk_level(7) == RiskRegisterItem.LEVEL_MEDIUM
    assert RiskScoringService.risk_level(12) == RiskRegisterItem.LEVEL_HIGH
    assert RiskScoringService.risk_level(20) == RiskRegisterItem.LEVEL_CRITICAL
    with pytest.raises(RiskComplianceValidationError):
        RiskScoringService.compute_score(likelihood=6, impact=1)

    risk = RiskRegisterItem.objects.create(
        org=org,
        risk_code="RISK-001",
        title="critical leak",
        likelihood=5,
        impact=5,
        inherent_score=25,
        residual_score=25,
        risk_level=RiskRegisterItem.LEVEL_CRITICAL,
        status=RiskRegisterItem.STATUS_OPEN,
        created_by=actor,
        updated_by=actor,
    )
    mitigation = RiskMitigationAction.objects.create(
        risk=risk,
        title="Fix",
        status=RiskMitigationAction.STATUS_IN_PROGRESS,
        due_at=timezone.now() - timedelta(days=1),
        effectiveness_score=80,
    )

    mit_svc = RiskMitigationService()
    count = mit_svc.mark_overdue(org_id=org.id)
    assert count == 1
    mitigation.refresh_from_db()
    assert mitigation.status == RiskMitigationAction.STATUS_OVERDUE

    mitigation.status = RiskMitigationAction.STATUS_IN_PROGRESS
    mitigation.save(update_fields=["status"])
    done, updated_risk = mit_svc.complete_action(action=mitigation, effectiveness_score=80)
    assert done.status == RiskMitigationAction.STATUS_COMPLETED
    assert updated_risk.residual_score <= updated_risk.inherent_score
    assert updated_risk.status in [RiskRegisterItem.STATUS_MONITORING, RiskRegisterItem.STATUS_MITIGATING]

    terminal_risk = RiskRegisterItem.objects.create(
        org=org,
        risk_code="RISK-TERM",
        title="done",
        likelihood=1,
        impact=1,
        inherent_score=1,
        residual_score=1,
        risk_level=RiskRegisterItem.LEVEL_LOW,
        status=RiskRegisterItem.STATUS_CLOSED,
        created_by=actor,
        updated_by=actor,
    )
    with pytest.raises(RiskComplianceValidationError):
        mit_svc.create_action(risk=terminal_risk, title="should fail")

    created_alerts = generate_risk_compliance_alerts(org_id=org.id)
    assert any(a.alert_type == RiskComplianceAlert.TYPE_CRITICAL_RISK for a in created_alerts)
    before = RiskComplianceAlert.objects.count()
    generate_risk_compliance_alerts(org_id=org.id)
    assert RiskComplianceAlert.objects.count() == before


@pytest.mark.django_db
@pytest.mark.unit
def test_legal_audit_dashboard_and_alert_lifecycle():
    org = create_org("Legal Org")
    actor = create_user(org, email="legal@example.com")

    requirement = ComplianceRequirement.objects.create(
        org=org,
        requirement_code="CR-DASH-01",
        title="Req",
        frequency_type=ComplianceRequirement.FREQ_MONTHLY,
        frequency_interval=1,
        status=ComplianceRequirement.STATUS_ACTIVE,
        next_run_at=timezone.now(),
        created_by=actor,
        updated_by=actor,
    )
    ComplianceCheck.objects.create(requirement=requirement, due_at=timezone.now(), status=ComplianceCheck.STATUS_COMPLIANT)
    ComplianceCheck.objects.create(requirement=requirement, due_at=timezone.now(), status=ComplianceCheck.STATUS_NON_COMPLIANT)
    ComplianceCheck.objects.create(requirement=requirement, due_at=timezone.now(), status=ComplianceCheck.STATUS_OVERDUE)

    legal = LegalContractRecord.objects.create(
        org=org,
        record_code="LC-001",
        title="Permit",
        record_type=LegalContractRecord.TYPE_PERMIT,
        expiry_date=timezone.now().date() - timedelta(days=1),
        renewal_due_at=timezone.now() - timedelta(days=3),
        status=LegalContractRecord.STATUS_ACTIVE,
        created_by=actor,
        updated_by=actor,
    )
    legal = update_legal_status(legal)
    assert legal.status == LegalContractRecord.STATUS_EXPIRED

    risk = RiskRegisterItem.objects.create(
        org=org,
        risk_code="RISK-DB-1",
        title="Risk",
        likelihood=4,
        impact=5,
        inherent_score=20,
        residual_score=20,
        risk_level=RiskRegisterItem.LEVEL_CRITICAL,
        status=RiskRegisterItem.STATUS_OPEN,
        created_by=actor,
        updated_by=actor,
    )
    RiskMitigationAction.objects.create(risk=risk, title="Mitigate", status=RiskMitigationAction.STATUS_OVERDUE)

    audit = AuditRecord.objects.create(
        org=org,
        audit_code="AR-001",
        title="Safety Audit",
        result=AuditRecord.RESULT_FAIL,
        score=Decimal("48.00"),
        findings_summary="findings",
        corrective_actions_required=True,
        created_by=actor,
    )

    dashboard = RiskComplianceDashboardService()
    summary = dashboard.summary(org_id=org.id)
    assert summary["total_requirements"] == 1
    assert summary["compliant_checks"] == 1
    assert summary["non_compliant_checks"] == 1
    assert summary["overdue_checks"] == 1
    assert summary["critical_risks"] >= 1
    assert summary["audit_findings_count"] == 1

    risk_summary = dashboard.risk_summary(org_id=org.id)
    assert risk_summary["CRITICAL"] >= 1

    legal_expiry = dashboard.legal_expiry(org_id=org.id)
    assert legal_expiry["expired_count"] >= 1

    alert_service = RiskComplianceAlertService()
    a1 = alert_service.create_alert(
        org_id=org.id,
        alert_type=RiskComplianceAlert.TYPE_AUDIT_CORRECTIVE,
        severity=RiskComplianceAlert.SEVERITY_HIGH,
        entity_type="audit_record",
        entity_id=str(audit.id),
        message="needs action",
    )
    assert a1 is not None
    a2 = alert_service.create_alert(
        org_id=org.id,
        alert_type=RiskComplianceAlert.TYPE_AUDIT_CORRECTIVE,
        severity=RiskComplianceAlert.SEVERITY_HIGH,
        entity_type="audit_record",
        entity_id=str(audit.id),
        message="duplicate",
    )
    assert a2 is None

    ack = alert_service.acknowledge(org_id=org.id, alert_id=a1.id)
    assert ack.status == RiskComplianceAlert.STATUS_ACKNOWLEDGED
    res = alert_service.resolve(org_id=org.id, alert_id=a1.id)
    assert res.status == RiskComplianceAlert.STATUS_RESOLVED
