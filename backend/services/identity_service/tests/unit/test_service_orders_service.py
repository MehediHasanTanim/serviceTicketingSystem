from decimal import Decimal

import pytest

from application.services.service_orders import (
    CostCalculator,
    LifecycleRuleValidator,
    ServiceOrderFilters,
    ServiceOrderService,
    ServiceOrderTransitionError,
    ServiceOrderValidationError,
)
from infrastructure.db.core.models import ServiceOrder, ServiceOrderAssignmentHistory, ServiceOrderStatusHistory
from tests.unit.api_test_helpers import create_org, create_user


@pytest.mark.django_db
@pytest.mark.unit
def test_lifecycle_rules_valid_and_invalid_transitions():
    validator = LifecycleRuleValidator()
    validator.validate(ServiceOrder.STATUS_OPEN, ServiceOrder.STATUS_ASSIGNED)
    with pytest.raises(ServiceOrderTransitionError):
        validator.validate(ServiceOrder.STATUS_OPEN, ServiceOrder.STATUS_COMPLETED)
    with pytest.raises(ServiceOrderTransitionError):
        validator.validate(ServiceOrder.STATUS_COMPLETED, ServiceOrder.STATUS_OPEN)
    with pytest.raises(ServiceOrderTransitionError):
        validator.validate(ServiceOrder.STATUS_VOID, ServiceOrder.STATUS_ASSIGNED)


@pytest.mark.django_db
@pytest.mark.unit
def test_cost_calculator_handles_decimals_and_negative_validation():
    calc = CostCalculator()
    result = calc.calculate(parts_cost="10.10", labor_cost="20.20", compensation_cost="3.30")
    assert result["total_cost"] == Decimal("33.60")
    with pytest.raises(ServiceOrderValidationError):
        calc.calculate(parts_cost="-1", labor_cost="0", compensation_cost="0")


@pytest.mark.django_db
@pytest.mark.unit
def test_assignment_reassignment_history_and_same_assignee_edge_case():
    org = create_org("Service Org")
    actor = create_user(org, email="actor@example.com")
    assignee_a = create_user(org, email="a@example.com")
    assignee_b = create_user(org, email="b@example.com")
    service = ServiceOrderService()
    order = service.create_order(
        created_by=actor,
        org_id=org.id,
        title="Fix AC",
        description="Room AC failure",
        customer_id=1001,
        assigned_to=assignee_a,
    )
    assert order.status == ServiceOrder.STATUS_ASSIGNED
    assert ServiceOrderAssignmentHistory.objects.filter(service_order=order).count() == 1

    service.assign(order=order, assignee=assignee_a, actor=actor, reason="same")
    assert ServiceOrderAssignmentHistory.objects.filter(service_order=order).count() == 1

    service.assign(order=order, assignee=assignee_b, actor=actor, reason="handover")
    assert ServiceOrderAssignmentHistory.objects.filter(service_order=order).count() == 2


@pytest.mark.django_db
@pytest.mark.unit
def test_create_update_filter_paginate_soft_delete_and_transitions():
    org = create_org("Service Org")
    actor = create_user(org, email="manager@example.com")
    assignee = create_user(org, email="worker@example.com")
    service = ServiceOrderService()

    created = []
    for idx in range(3):
        order = service.create_order(
            created_by=actor,
            org_id=org.id,
            title=f"Order {idx}",
            description="desc",
            customer_id=idx + 1,
            assigned_to=assignee if idx == 0 else None,
            priority=ServiceOrder.PRIORITY_HIGH if idx == 0 else ServiceOrder.PRIORITY_LOW,
            type=ServiceOrder.TYPE_REPAIR,
        )
        created.append(order)

    first = created[0]
    updated = service.update_order(order=first, title="Order 0 Updated")
    assert updated.title == "Order 0 Updated"

    filtered_qs = service.list_orders(
        filters=ServiceOrderFilters(org_id=org.id, priority=ServiceOrder.PRIORITY_HIGH)
    )
    assert filtered_qs.count() == 1

    paged = filtered_qs.order_by("id")[:1]
    assert len(paged) == 1

    service.transition(order=first, to_status=ServiceOrder.STATUS_IN_PROGRESS, actor=actor)
    service.transition(order=first, to_status=ServiceOrder.STATUS_COMPLETED, actor=actor)
    assert ServiceOrderStatusHistory.objects.filter(service_order=first).count() >= 2
    with pytest.raises(ServiceOrderTransitionError):
        service.transition(order=first, to_status=ServiceOrder.STATUS_ASSIGNED, actor=actor)

    service.soft_delete(order=created[2])
    assert ServiceOrder.objects.get(id=created[2].id).is_deleted is True
