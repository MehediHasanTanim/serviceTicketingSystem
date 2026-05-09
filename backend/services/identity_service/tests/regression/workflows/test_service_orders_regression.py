# Covers: BE-SO-001, BE-SO-002, BE-SO-003, BE-SO-004, BE-SO-006, BE-SO-011
import pytest

from tests.unit.test_api_service_orders import (
    test_service_order_costs_remarks_attachments_and_soft_delete,
    test_service_order_create_list_detail_update_flow,
    test_service_order_transitions_and_assignment_history,
)


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.service_orders
@pytest.mark.django_db
def test_be_so_001_core_create_list_detail_flow():
    test_service_order_create_list_detail_update_flow()


@pytest.mark.regression
@pytest.mark.p1
@pytest.mark.service_orders
@pytest.mark.django_db
def test_be_so_002_003_004_transition_and_assignment_rules():
    test_service_order_transitions_and_assignment_history()


@pytest.mark.regression
@pytest.mark.p1
@pytest.mark.service_orders
@pytest.mark.django_db
def test_be_so_006_011_costs_and_closure_related_validations():
    test_service_order_costs_remarks_attachments_and_soft_delete()
