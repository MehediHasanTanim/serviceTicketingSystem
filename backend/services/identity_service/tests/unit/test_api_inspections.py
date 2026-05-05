from django.urls import reverse

from infrastructure.db.core.models import AuditLog, InspectionTemplate, NonComplianceAlert
from tests.unit.api_test_helpers import authenticated_client, create_org, create_user, grant_permissions


def _grant_all(user):
    grant_permissions(
        user,
        [
            "inspections.templates.manage",
            "inspections.templates.view",
            "inspections.runs.manage",
            "inspections.runs.view",
            "inspections.runs.admin_override",
            "inspections.reports.view",
            "inspections.alerts.view",
            "inspections.alerts.manage",
            "audit.view",
        ],
        role_name="inspection-manager",
    )


def test_template_create_run_response_complete_and_audit(db):
    org = create_org("Ins API Org")
    actor = create_user(org, email="insp-api@example.com")
    _grant_all(actor)
    client = authenticated_client(actor)

    create_template = client.post(
        reverse("inspection-template-list-create"),
        {
            "org_id": org.id,
            "template_code": "TEMP-ROOM-01",
            "name": "Room QA",
            "category": "ROOM",
            "sections": [
                {
                    "title": "Safety",
                    "sort_order": 1,
                    "weight": "1.00",
                    "items": [
                        {
                            "question": "Door lock",
                            "response_type": "PASS_FAIL_NA",
                            "is_required": True,
                            "weight": "3.00",
                            "sort_order": 1,
                            "non_compliance_trigger": True,
                        }
                    ],
                }
            ],
        },
        format="json",
    )
    assert create_template.status_code == 201
    template_id = create_template.data["id"]

    run_create = client.post(
        reverse("inspection-run-list-create"),
        {
            "org_id": org.id,
            "template_id": template_id,
            "notes": "scheduled",
        },
        format="json",
    )
    assert run_create.status_code == 201
    run_id = run_create.data["id"]

    run_start = client.post(reverse("inspection-run-start", kwargs={"run_id": run_id}), {"org_id": org.id}, format="json")
    assert run_start.status_code == 200

    item_id = InspectionTemplate.objects.get(id=template_id).sections.first().items.first().id
    fail_response = client.post(
        reverse("inspection-run-responses", kwargs={"run_id": run_id}),
        {
            "org_id": org.id,
            "checklist_item_id": item_id,
            "response": "FAIL",
            "comment": "broken",
            "evidence_attachment_id": 42,
        },
        format="json",
    )
    assert fail_response.status_code == 201

    complete = client.post(reverse("inspection-run-complete", kwargs={"run_id": run_id}), {"org_id": org.id}, format="json")
    assert complete.status_code == 200
    assert complete.data["status"] == "COMPLETED"
    assert complete.data["result"] == "FAIL"

    assert NonComplianceAlert.objects.filter(inspection_run_id=run_id).exists()
    actions = set(AuditLog.objects.filter(org=org).values_list("action", flat=True))
    assert "inspection_template_created" in actions
    assert "inspection_response_submitted" in actions
    assert "inspection_run_completed" in actions


def test_reporting_and_alert_actions(db):
    org = create_org("Ins Reporting Org")
    actor = create_user(org, email="ins-report@example.com")
    _grant_all(actor)
    client = authenticated_client(actor)

    template = InspectionTemplate.objects.create(
        org=org,
        template_code="TEMP-001",
        name="Template",
        category="GEN",
        is_active=True,
        version=1,
        created_by=actor,
        updated_by=actor,
    )

    run_create = client.post(
        reverse("inspection-run-list-create"),
        {"org_id": org.id, "template_id": template.id},
        format="json",
    )
    run_id = run_create.data["id"]

    summary = client.get(reverse("inspection-report-summary"), {"org_id": org.id})
    assert summary.status_code == 200
    assert summary.data["total_inspections"] >= 1

    trends = client.get(reverse("inspection-report-trends"), {"org_id": org.id, "group_by": "day"})
    assert trends.status_code == 200
    assert "results" in trends.data

    alert = NonComplianceAlert.objects.create(
        org=org,
        inspection_run_id=run_id,
        alert_type=NonComplianceAlert.ALERT_FINAL_FAIL,
        severity=NonComplianceAlert.SEVERITY_HIGH,
        message="manual",
        status=NonComplianceAlert.STATUS_OPEN,
    )

    ack = client.post(reverse("inspection-alert-ack", kwargs={"alert_id": alert.id}), {"org_id": org.id}, format="json")
    assert ack.status_code == 200
    assert ack.data["status"] == NonComplianceAlert.STATUS_ACKNOWLEDGED

    res = client.post(reverse("inspection-alert-resolve", kwargs={"alert_id": alert.id}), {"org_id": org.id}, format="json")
    assert res.status_code == 200
    assert res.data["status"] == NonComplianceAlert.STATUS_RESOLVED


def test_admin_override_requires_permission(db):
    org = create_org("Ins Override Org")
    actor = create_user(org, email="ins-override@example.com")
    grant_permissions(actor, ["inspections.templates.manage", "inspections.runs.manage"], role_name="inspection-manager")
    client = authenticated_client(actor)

    create_template = client.post(
        reverse("inspection-template-list-create"),
        {
            "org_id": org.id,
            "template_code": "TEMP-OVR-01",
            "name": "Override QA",
            "sections": [{"title": "Safety", "items": [{"question": "Door lock", "is_required": True, "weight": "1.00"}]}],
        },
        format="json",
    )
    template_id = create_template.data["id"]
    run_create = client.post(reverse("inspection-run-list-create"), {"org_id": org.id, "template_id": template_id}, format="json")
    run_id = run_create.data["id"]
    client.post(reverse("inspection-run-start", kwargs={"run_id": run_id}), {"org_id": org.id}, format="json")
    item_id = InspectionTemplate.objects.get(id=template_id).sections.first().items.first().id
    client.post(
        reverse("inspection-run-responses", kwargs={"run_id": run_id}),
        {"org_id": org.id, "checklist_item_id": item_id, "response": "PASS", "comment": "ok"},
        format="json",
    )
    client.post(reverse("inspection-run-complete", kwargs={"run_id": run_id}), {"org_id": org.id}, format="json")
    override_response = client.post(
        reverse("inspection-run-responses", kwargs={"run_id": run_id}),
        {
            "org_id": org.id,
            "checklist_item_id": item_id,
            "response": "FAIL",
            "comment": "override",
            "evidence_attachment_id": 7,
            "admin_override": True,
        },
        format="json",
    )
    assert override_response.status_code == 403
