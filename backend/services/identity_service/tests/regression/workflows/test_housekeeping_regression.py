# Covers: BE-HK-001, BE-HK-002, BE-HK-003, BE-HK-004, BE-HK-007
import pytest

from tests.unit.test_api_housekeeping import (
    test_api_room_status_task_generation_and_kpi_envelope_and_audit,
    test_housekeeping_task_list_detail_and_lifecycle_endpoints,
)


@pytest.mark.regression
@pytest.mark.p1
@pytest.mark.housekeeping
@pytest.mark.django_db
def test_be_hk_001_002_room_status_and_task_generation():
    test_api_room_status_task_generation_and_kpi_envelope_and_audit()


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.housekeeping
@pytest.mark.django_db
def test_be_hk_003_lifecycle_progression():
    test_housekeeping_task_list_detail_and_lifecycle_endpoints()
