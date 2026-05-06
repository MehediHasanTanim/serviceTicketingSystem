import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from infrastructure.db.core.models import AuditLog, FoodBeverageBreakfastCount, FoodBeverageOutletReadiness, FoodBeverageTask
from tests.unit.api_test_helpers import authenticated_client, create_org, create_user, grant_permissions


@pytest.mark.django_db
@pytest.mark.unit
def test_fb_breakfast_counts_crud_and_filters_and_audit():
    org = create_org("FB Breakfast Org")
    actor = create_user(org, email="fb.breakfast@example.com")
    grant_permissions(actor, ["audit.view"], role_name="fb-manager")
    prop = org.properties.create(code="PFB1", name="FB Prop", timezone="UTC", address_line1="x", city="x", country="x")
    client = authenticated_client(actor)

    create_1 = client.post(
        reverse("fb-breakfast-list-create"),
        {
            "org_id": org.id,
            "property_id": prop.id,
            "outlet_id": 101,
            "service_date": "2026-05-01",
            "expected_guest_count": 100,
            "actual_guest_count": 90,
            "in_house_guest_count": 95,
            "complimentary_count": 20,
            "paid_count": 70,
            "no_show_count": 5,
            "notes": "rainy day",
        },
        format="json",
    )
    assert create_1.status_code == status.HTTP_201_CREATED
    row_id = create_1.data["id"]

    create_2 = client.post(
        reverse("fb-breakfast-list-create"),
        {
            "org_id": org.id,
            "property_id": prop.id,
            "outlet_id": 102,
            "service_date": "2026-05-02",
            "expected_guest_count": 110,
            "actual_guest_count": 115,
            "in_house_guest_count": 112,
            "complimentary_count": 15,
            "paid_count": 100,
            "no_show_count": 2,
        },
        format="json",
    )
    assert create_2.status_code == status.HTTP_201_CREATED

    listed = client.get(reverse("fb-breakfast-list-create"), {"org_id": org.id, "outlet_id": 101, "page": 1, "page_size": 10})
    assert listed.status_code == status.HTTP_200_OK
    assert listed.data["count"] == 1
    assert listed.data["results"][0]["id"] == row_id

    detail = client.get(reverse("fb-breakfast-detail", kwargs={"id": row_id}), {"org_id": org.id})
    assert detail.status_code == status.HTTP_200_OK
    assert detail.data["outlet_id"] == 101

    patched = client.patch(
        reverse("fb-breakfast-detail", kwargs={"id": row_id}),
        {"org_id": org.id, "actual_guest_count": 92, "notes": "updated"},
        format="json",
    )
    assert patched.status_code == status.HTTP_200_OK
    assert patched.data["actual_guest_count"] == 92

    assert FoodBeverageBreakfastCount.objects.filter(org=org).count() == 2
    actions = set(AuditLog.objects.filter(org=org).values_list("action", flat=True))
    assert "breakfast_count_created" in actions
    assert "breakfast_count_updated" in actions


@pytest.mark.django_db
@pytest.mark.unit
def test_fb_outlet_readiness_crud_checklist_actions_and_audit():
    org = create_org("FB Readiness Org")
    actor = create_user(org, email="fb.readiness@example.com")
    prop = org.properties.create(code="PFB2", name="FB Prop 2", timezone="UTC", address_line1="x", city="x", country="x")
    client = authenticated_client(actor)

    created = client.post(
        reverse("fb-readiness-list-create"),
        {
            "org_id": org.id,
            "property_id": prop.id,
            "outlet_id": 201,
            "readiness_date": "2026-05-01",
            "shift": "BREAKFAST",
            "checklist_items": [
                {"id": 1, "name": "Station setup", "category": "SERVICE_SETUP", "is_required": True},
                {"id": 2, "name": "Clean counter", "category": "CLEANLINESS", "is_required": True},
            ],
        },
        format="json",
    )
    assert created.status_code == status.HTTP_201_CREATED
    rid = created.data["id"]

    updated_item = client.patch(
        reverse("fb-readiness-detail", kwargs={"id": rid}),
        {"org_id": org.id, "checklist_item_id": 1, "result": "PASS", "comment": "ok"},
        format="json",
    )
    assert updated_item.status_code == status.HTTP_200_OK
    assert updated_item.data["checklist_score"] >= 0

    start = client.post(reverse("fb-readiness-start", kwargs={"id": rid}), {"org_id": org.id}, format="json")
    submit = client.post(reverse("fb-readiness-submit", kwargs={"id": rid}), {"org_id": org.id}, format="json")
    verify = client.post(reverse("fb-readiness-verify", kwargs={"id": rid}), {"org_id": org.id}, format="json")
    void = client.post(reverse("fb-readiness-void", kwargs={"id": rid}), {"org_id": org.id, "reason": "duplicate"}, format="json")

    assert start.status_code == status.HTTP_200_OK
    assert submit.status_code == status.HTTP_200_OK
    assert verify.status_code == status.HTTP_200_OK
    assert void.status_code == status.HTTP_200_OK
    assert void.data["status"] == "VOID"

    actions = set(AuditLog.objects.filter(org=org).values_list("action", flat=True))
    assert "outlet_readiness_created" in actions
    assert "outlet_readiness_start" in actions
    assert "outlet_readiness_submit" in actions
    assert "outlet_readiness_verify" in actions
    assert "outlet_readiness_void" in actions


@pytest.mark.django_db
@pytest.mark.unit
def test_fb_tasks_crud_assign_lifecycle_metrics_and_audit_filters():
    org = create_org("FB Tasks Org")
    actor = create_user(org, email="fb.tasks@example.com")
    assignee = create_user(org, email="fb.worker@example.com")
    prop = org.properties.create(code="PFB3", name="FB Prop 3", timezone="UTC", address_line1="x", city="x", country="x")
    grant_permissions(actor, ["audit.view"], role_name="fb-manager")
    client = authenticated_client(actor)

    created = client.post(
        reverse("fb-task-list-create"),
        {
            "org_id": org.id,
            "property_id": prop.id,
            "outlet_id": 301,
            "title": "Prep buffet line",
            "task_type": "BREAKFAST_PREP",
            "priority": "HIGH",
        },
        format="json",
    )
    assert created.status_code == status.HTTP_201_CREATED
    task_id = created.data["id"]

    listed = client.get(reverse("fb-task-list-create"), {"org_id": org.id, "q": "buffet", "status": "PENDING"})
    assert listed.status_code == status.HTTP_200_OK
    assert listed.data["count"] == 1

    assign = client.post(
        reverse("fb-task-assign", kwargs={"id": task_id}),
        {"org_id": org.id, "assignee_id": assignee.id, "reason": "shift allocation"},
        format="json",
    )
    assert assign.status_code == status.HTTP_200_OK
    assert assign.data["assigned_to"] == assignee.id

    start = client.post(reverse("fb-task-start", kwargs={"id": task_id}), {"org_id": org.id}, format="json")
    complete = client.post(reverse("fb-task-complete", kwargs={"id": task_id}), {"org_id": org.id}, format="json")
    assert start.status_code == status.HTTP_200_OK
    assert complete.status_code == status.HTTP_200_OK
    assert complete.data["status"] == "COMPLETED"

    cancelled = client.post(
        reverse("fb-task-cancel", kwargs={"id": task_id}),
        {"org_id": org.id, "reason": "late cancellation"},
        format="json",
    )
    assert cancelled.status_code == status.HTTP_200_OK
    assert cancelled.data["status"] == "CANCELLED"

    voided = client.post(
        reverse("fb-task-void", kwargs={"id": task_id}),
        {"org_id": org.id, "reason": "invalid task"},
        format="json",
    )
    assert voided.status_code == status.HTTP_200_OK
    assert voided.data["status"] == "VOID"

    # Metrics endpoints
    summary = client.get(reverse("fb-metrics-summary"), {"org_id": org.id})
    breakfast = client.get(reverse("fb-metrics-breakfast"), {"org_id": org.id})
    readiness = client.get(reverse("fb-metrics-readiness"), {"org_id": org.id})
    tasks = client.get(reverse("fb-metrics-tasks"), {"org_id": org.id})

    assert summary.status_code == status.HTTP_200_OK
    assert "total_tasks" in summary.data
    assert breakfast.status_code == status.HTTP_200_OK
    assert readiness.status_code == status.HTTP_200_OK
    assert tasks.status_code == status.HTTP_200_OK

    # Audit filtering: ensure one F&B action is queryable
    audit = client.get(
        reverse("fb-audit-logs"),
        {
            "org_id": org.id,
            "action": "fb_task_assigned",
            "target_type": "food_beverage_task",
            "page": 1,
            "page_size": 20,
        },
    )
    assert audit.status_code == status.HTTP_200_OK
    assert audit.data["count"] >= 1
    assert any(row["action"] == "fb_task_assigned" for row in audit.data["results"])

    # Date range filter still returns shape
    today = timezone.now().date().isoformat()
    audit_by_date = client.get(reverse("fb-audit-logs"), {"org_id": org.id, "date_from": today, "date_to": today})
    assert audit_by_date.status_code == status.HTTP_200_OK
    assert "results" in audit_by_date.data

    assert FoodBeverageTask.objects.filter(org=org).count() == 1
    assert FoodBeverageOutletReadiness.objects.filter(org=org).count() == 0
