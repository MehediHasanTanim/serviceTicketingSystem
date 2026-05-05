import pytest
from django.urls import reverse
from rest_framework import status

from infrastructure.db.core.models import AuditLog, GuestComplaint
from tests.unit.api_test_helpers import authenticated_client, create_org, create_user, grant_permissions


@pytest.mark.django_db
@pytest.mark.unit
def test_guest_complaint_create_transition_escalate_confirm_and_audit_events():
    org = create_org("GC API Org")
    actor = create_user(org, email="gc.api@example.com")
    assignee = create_user(org, email="gc.assignee@example.com")
    prop = org.properties.create(code="PGC", name="PropGC", timezone="UTC", address_line1="x", city="x", country="x")
    grant_permissions(actor, ["guest_complaints.manage", "guest_complaints.view", "audit.view"], role_name="gc-manager")
    client = authenticated_client(actor)

    create_res = client.post(
        reverse("guest-complaint-list-create"),
        {
            "org_id": org.id,
            "guest_name": "Guest X",
            "property_id": prop.id,
            "category": "MAINTENANCE",
            "severity": "HIGH",
            "title": "AC issue",
            "source": "PHONE",
        },
        format="json",
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    complaint_id = create_res.data["id"]

    assign_res = client.post(
        reverse("guest-complaint-assign", kwargs={"complaint_id": complaint_id}),
        {"org_id": org.id, "assignee_id": assignee.id, "reason": "shift"},
        format="json",
    )
    assert assign_res.status_code == status.HTTP_200_OK

    start_res = client.post(reverse("guest-complaint-start", kwargs={"complaint_id": complaint_id}), {"org_id": org.id}, format="json")
    assert start_res.status_code == status.HTTP_200_OK

    resolve_res = client.post(reverse("guest-complaint-resolve", kwargs={"complaint_id": complaint_id}), {"org_id": org.id}, format="json")
    assert resolve_res.status_code == status.HTTP_200_OK

    escalate_res = client.post(
        reverse("guest-complaint-escalate", kwargs={"complaint_id": complaint_id}),
        {"org_id": org.id, "reason": "manual escalation"},
        format="json",
    )
    assert escalate_res.status_code == status.HTTP_200_OK

    complaint = GuestComplaint.objects.get(id=complaint_id)
    complaint.status = GuestComplaint.STATUS_RESOLVED
    complaint.save(update_fields=["status", "updated_at"])

    confirm_res = client.post(
        reverse("guest-complaint-confirm-resolution", kwargs={"complaint_id": complaint_id}),
        {"org_id": org.id, "satisfaction_score": "4.50", "satisfaction_comment": "good"},
        format="json",
    )
    assert confirm_res.status_code == status.HTTP_200_OK

    logs = AuditLog.objects.filter(org=org, target_type="guest_complaint", target_id=str(complaint_id))
    actions = set(logs.values_list("action", flat=True))
    assert "complaint_created" in actions
    assert "complaint_status_changed" in actions
    assert "complaint_escalated" in actions
    assert "complaint_confirmed" in actions


@pytest.mark.django_db
@pytest.mark.unit
def test_guest_complaint_analytics_endpoints_and_escalation_run():
    org = create_org("GC Analytics")
    actor = create_user(org, email="gc.analytics@example.com")
    prop = org.properties.create(code="PGA", name="PropGA", timezone="UTC", address_line1="x", city="x", country="x")
    grant_permissions(actor, ["guest_complaints.manage", "guest_complaints.view", "audit.view"], role_name="gc-manager")
    client = authenticated_client(actor)

    client.post(
        reverse("guest-complaint-list-create"),
        {
            "org_id": org.id,
            "guest_name": "Guest A",
            "property_id": prop.id,
            "category": "NOISE",
            "severity": "MEDIUM",
            "title": "Noise",
            "source": "PHONE",
        },
        format="json",
    )

    summary = client.get(reverse("guest-complaint-analytics-summary"), {"org_id": org.id})
    trends = client.get(reverse("guest-complaint-analytics-trends"), {"org_id": org.id})
    rt = client.get(reverse("guest-complaint-analytics-resolution-time"), {"org_id": org.id})
    sat = client.get(reverse("guest-complaint-analytics-satisfaction"), {"org_id": org.id})
    run = client.post(reverse("guest-complaint-escalation-run"), {"org_id": org.id}, format="json")

    assert summary.status_code == status.HTTP_200_OK
    assert trends.status_code == status.HTTP_200_OK
    assert rt.status_code == status.HTTP_200_OK
    assert sat.status_code == status.HTTP_200_OK
    assert run.status_code == status.HTTP_200_OK
    assert "checked_count" in run.data
