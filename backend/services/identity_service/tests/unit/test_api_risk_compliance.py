import pytest
from django.urls import reverse

from infrastructure.db.core.models import AuditLog
from tests.unit.api_test_helpers import authenticated_client, create_org, create_user, grant_permissions


@pytest.mark.django_db
@pytest.mark.unit
def test_risk_compliance_api_flow_and_audit_logs():
    org = create_org("RC API Org")
    actor = create_user(org, email="rc-api@example.com")
    grant_permissions(
        actor,
        [
            "risk_compliance.requirements.manage",
            "risk_compliance.requirements.view",
            "risk_compliance.schedules.run",
            "risk_compliance.checks.manage",
            "risk_compliance.checks.view",
            "risk_compliance.risks.manage",
            "risk_compliance.risks.view",
            "risk_compliance.legal.manage",
            "risk_compliance.legal.view",
            "risk_compliance.audit_records.manage",
            "risk_compliance.audit_records.view",
            "risk_compliance.dashboard.view",
            "risk_compliance.alerts.view",
            "risk_compliance.alerts.manage",
            "risk_compliance.approvals.manage",
            "audit.view",
        ],
        role_name="risk-compliance-manager",
    )
    client = authenticated_client(actor)

    create_req = client.post(
        reverse("risk-compliance-requirements"),
        {
            "org_id": org.id,
            "requirement_code": "RC-REQ-001",
            "title": "Fire compliance",
            "frequency_type": "DAILY",
            "checklist_items": [{"title": "Upload evidence", "is_required": True, "evidence_required": True}],
        },
        format="json",
    )
    assert create_req.status_code == 201
    req_id = create_req.data["id"]

    schedule = client.post(reverse("risk-compliance-schedule-run"), {"org_id": org.id}, format="json")
    assert schedule.status_code == 200

    checks = client.get(reverse("risk-compliance-checks"), {"org_id": org.id, "page": 1, "page_size": 10})
    assert checks.status_code == 200
    assert checks.data["count"] == 1
    assert checks.data["page"] == 1
    assert checks.data["page_size"] == 10
    check_id = checks.data["results"][0]["id"]

    submit = client.post(
        reverse("risk-compliance-check-submit", kwargs={"id": check_id}),
        {"org_id": org.id, "compliant": False, "evidence_attachment_id": 15, "notes": "failed check"},
        format="json",
    )
    assert submit.status_code == 200
    assert submit.data["status"] == "NON_COMPLIANT"

    create_risk = client.post(
        reverse("risk-compliance-risks"),
        {
            "org_id": org.id,
            "risk_code": "RC-RISK-1",
            "title": "Critical exposure",
            "likelihood": 5,
            "impact": 5,
        },
        format="json",
    )
    assert create_risk.status_code == 201
    risk_id = create_risk.data["id"]

    mitigation = client.post(
        reverse("risk-compliance-risk-mitigations", kwargs={"id": risk_id}),
        {"org_id": org.id, "title": "Patch now", "effectiveness_score": 85},
        format="json",
    )
    assert mitigation.status_code == 201

    legal = client.post(
        reverse("risk-compliance-legal-records"),
        {
            "org_id": org.id,
            "record_code": "RC-LGL-1",
            "title": "Permit A",
            "record_type": "PERMIT",
        },
        format="json",
    )
    assert legal.status_code == 201
    legal_id = legal.data["id"]

    legal_upd = client.patch(
        reverse("risk-compliance-legal-record-detail", kwargs={"id": legal_id}),
        {"org_id": org.id, "notes": "updated"},
        format="json",
    )
    assert legal_upd.status_code == 200
    assert legal_upd.data["notes"] == "updated"

    audit_record = client.post(
        reverse("risk-compliance-audit-records"),
        {
            "org_id": org.id,
            "audit_code": "RC-AUD-1",
            "title": "Audit one",
            "result": "FAIL",
            "corrective_actions_required": True,
        },
        format="json",
    )
    assert audit_record.status_code == 201

    alerts = client.get(reverse("risk-compliance-alerts"), {"org_id": org.id})
    assert alerts.status_code == 200
    assert alerts.data["count"] >= 1
    alert_id = alerts.data["results"][0]["id"]

    ack = client.post(reverse("risk-compliance-alert-ack", kwargs={"id": alert_id}), {"org_id": org.id}, format="json")
    assert ack.status_code == 200
    resolve = client.post(reverse("risk-compliance-alert-resolve", kwargs={"id": alert_id}), {"org_id": org.id}, format="json")
    assert resolve.status_code == 200

    audit_logs = client.get(reverse("risk-compliance-audit-logs"), {"org_id": org.id})
    assert audit_logs.status_code == 200
    assert "page" in audit_logs.data
    assert "page_size" in audit_logs.data

    trail_post = client.post(
        reverse("risk-compliance-approval-trails"),
        {"org_id": org.id, "entity_type": "compliance_check", "entity_id": str(check_id), "decision": "APPROVE", "comment": "approved by manager"},
        format="json",
    )
    assert trail_post.status_code == 200
    trail_get = client.get(reverse("risk-compliance-approval-trails"), {"org_id": org.id, "entity_type": "compliance_check", "entity_id": str(check_id)})
    assert trail_get.status_code == 200
    assert trail_get.data["count"] >= 1
    actions = set(AuditLog.objects.filter(org=org).values_list("action", flat=True))
    assert "risk_compliance_compliance_requirement_created" in actions
    assert "risk_compliance_compliance_check_submitted" in actions
    assert "risk_compliance_risk_score_calculated" in actions
    assert "risk_compliance_legal_record_updated" in actions
    assert "risk_compliance_risk_compliance_alert_resolved" in actions


@pytest.mark.django_db
@pytest.mark.unit
def test_dashboard_zero_safe_values():
    org = create_org("RC Zero Org")
    actor = create_user(org, email="rc-zero@example.com")
    grant_permissions(actor, ["risk_compliance.dashboard.view"], role_name="risk-compliance-viewer")
    client = authenticated_client(actor)
    resp = client.get(reverse("risk-compliance-dashboard-summary"), {"org_id": org.id})
    assert resp.status_code == 200
    assert resp.data["total_requirements"] == 0
    assert resp.data["compliance_rate"] == 0.0
    assert resp.data["open_risks"] == 0
