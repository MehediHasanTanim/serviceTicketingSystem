import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from infrastructure.db.core.models import AuditLog, ServiceOrder, ServiceOrderAssignmentHistory
from tests.unit.api_test_helpers import authenticated_client, create_org, create_user, grant_permissions


@pytest.mark.django_db
@pytest.mark.unit
def test_service_order_create_list_detail_update_flow():
    org = create_org("Orders Org")
    actor = create_user(org, email="manager@example.com")
    assignee = create_user(org, email="assignee@example.com")
    grant_permissions(actor, ["service_orders.manage", "service_orders.view"], role_name="manager")
    client = authenticated_client(actor)

    create_res = client.post(
        reverse("service-order-list-create"),
        {
            "org_id": org.id,
            "title": "Broken Door",
            "description": "Door handle broken",
            "customer_id": 123,
            "assigned_to": assignee.id,
            "priority": "HIGH",
            "type": "REPAIR",
        },
        format="json",
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    order_id = create_res.data["id"]
    assert create_res.data["status"] == "ASSIGNED"

    list_res = client.get(reverse("service-order-list-create"), {"org_id": org.id, "status": "ASSIGNED"})
    assert list_res.status_code == status.HTTP_200_OK
    assert list_res.data["count"] == 1

    detail_res = client.get(reverse("service-order-detail", kwargs={"order_id": order_id}), {"org_id": org.id})
    assert detail_res.status_code == status.HTTP_200_OK
    assert detail_res.data["title"] == "Broken Door"

    patch_res = client.patch(
        reverse("service-order-detail", kwargs={"order_id": order_id}),
        {"org_id": org.id, "title": "Broken Main Door"},
        format="json",
    )
    assert patch_res.status_code == status.HTTP_200_OK
    assert patch_res.data["title"] == "Broken Main Door"


@pytest.mark.django_db
@pytest.mark.unit
def test_service_order_transitions_and_assignment_history():
    org = create_org("Orders Org")
    actor = create_user(org, email="manager2@example.com")
    assignee = create_user(org, email="worker1@example.com")
    assignee2 = create_user(org, email="worker2@example.com")
    grant_permissions(actor, ["service_orders.manage", "service_orders.view"], role_name="manager")
    client = authenticated_client(actor)

    create_res = client.post(
        reverse("service-order-list-create"),
        {"org_id": org.id, "title": "Network Issue", "description": "", "customer_id": 456, "assigned_to": assignee.id},
        format="json",
    )
    order_id = create_res.data["id"]

    start_res = client.post(
        reverse("service-order-start", kwargs={"order_id": order_id}),
        {"org_id": org.id},
        format="json",
    )
    assert start_res.status_code == status.HTTP_200_OK
    assert start_res.data["status"] == "IN_PROGRESS"

    complete_res = client.post(
        reverse("service-order-complete", kwargs={"order_id": order_id}),
        {"org_id": org.id},
        format="json",
    )
    assert complete_res.status_code == status.HTTP_200_OK
    assert complete_res.data["status"] == "COMPLETED"

    invalid_res = client.post(
        reverse("service-order-start", kwargs={"order_id": order_id}),
        {"org_id": org.id},
        format="json",
    )
    assert invalid_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid transition" in invalid_res.data["detail"]

    second = client.post(
        reverse("service-order-list-create"),
        {"org_id": org.id, "title": "Printer Issue", "description": "", "customer_id": 789, "assigned_to": assignee.id},
        format="json",
    )
    second_id = second.data["id"]
    reassign_res = client.post(
        reverse("service-order-reassign", kwargs={"order_id": second_id}),
        {"org_id": org.id, "assignee_id": assignee2.id, "reason": "new shift"},
        format="json",
    )
    assert reassign_res.status_code == status.HTTP_200_OK
    assert reassign_res.data["assigned_to"] == assignee2.id
    order = ServiceOrder.objects.get(id=second_id)
    assert ServiceOrderAssignmentHistory.objects.filter(service_order=order).count() == 2


@pytest.mark.django_db
@pytest.mark.unit
def test_service_order_costs_remarks_attachments_and_soft_delete():
    org = create_org("Orders Org")
    actor = create_user(org, email="manager3@example.com")
    grant_permissions(actor, ["service_orders.manage", "service_orders.view"], role_name="manager")
    client = authenticated_client(actor)

    create_res = client.post(
        reverse("service-order-list-create"),
        {"org_id": org.id, "title": "Leakage", "description": "", "customer_id": 600},
        format="json",
    )
    order_id = create_res.data["id"]

    costs_res = client.patch(
        reverse("service-order-costs", kwargs={"order_id": order_id}),
        {"org_id": org.id, "parts_cost": "10.50", "labor_cost": "20.25", "compensation_cost": "1.25"},
        format="json",
    )
    assert costs_res.status_code == status.HTTP_200_OK
    assert str(costs_res.data["total_cost"]) == "32.00"

    bad_costs = client.patch(
        reverse("service-order-costs", kwargs={"order_id": order_id}),
        {"org_id": org.id, "parts_cost": "-1.00", "labor_cost": "0.00", "compensation_cost": "0.00"},
        format="json",
    )
    assert bad_costs.status_code == status.HTTP_400_BAD_REQUEST

    remark_res = client.post(
        reverse("service-order-remarks", kwargs={"order_id": order_id}),
        {"org_id": org.id, "text": "Investigating", "is_internal": True},
        format="json",
    )
    assert remark_res.status_code == status.HTTP_201_CREATED
    remarks_list = client.get(reverse("service-order-remarks", kwargs={"order_id": order_id}), {"org_id": org.id})
    assert remarks_list.status_code == status.HTTP_200_OK
    assert remarks_list.data["count"] == 1

    attachment_res = client.post(
        reverse("service-order-attachments", kwargs={"order_id": order_id}),
        {"org_id": org.id, "file_name": "photo.jpg", "storage_key": "uploads/photo.jpg"},
        format="json",
    )
    assert attachment_res.status_code == status.HTTP_201_CREATED

    delete_res = client.delete(reverse("service-order-detail", kwargs={"order_id": order_id}), {"org_id": org.id})
    assert delete_res.status_code == status.HTTP_204_NO_CONTENT
    assert ServiceOrder.objects.get(id=order_id).is_deleted is True


@pytest.mark.django_db
@pytest.mark.unit
def test_service_order_actions_are_recorded_in_audit_logs():
    org = create_org("Orders Audit Org")
    actor = create_user(org, email="audit-manager@example.com")
    assignee = create_user(org, email="audit-assignee@example.com")
    grant_permissions(actor, ["service_orders.manage", "service_orders.view", "audit.view"], role_name="manager")
    client = APIClient()
    client.force_authenticate(user=actor)

    create_res = client.post(
        reverse("service-order-list-create"),
        {"org_id": org.id, "title": "Audit me", "description": "", "customer_id": 12},
        format="json",
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    order_id = create_res.data["id"]

    assign_res = client.post(
        reverse("service-order-assign", kwargs={"order_id": order_id}),
        {"org_id": org.id, "assignee_id": assignee.id, "reason": "load balancing"},
        format="json",
    )
    assert assign_res.status_code == status.HTTP_200_OK

    costs_res = client.patch(
        reverse("service-order-costs", kwargs={"order_id": order_id}),
        {"org_id": org.id, "parts_cost": "1.00", "labor_cost": "2.00", "compensation_cost": "3.00"},
        format="json",
    )
    assert costs_res.status_code == status.HTTP_200_OK

    logs = AuditLog.objects.filter(org=org, target_type="service_order", target_id=str(order_id))
    actions = set(logs.values_list("action", flat=True))
    assert "service_order.created" in actions
    assert "service_order.assigned" in actions
    assert "service_order.costs_updated" in actions
