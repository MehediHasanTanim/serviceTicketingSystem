# Covers: BE-INT-001, BE-INT-002, BE-INT-004, BE-INT-005, BE-INT-007, BE-INT-008
import pytest

from tests.unit.test_api_integrations import (
    test_dead_letter_and_manual_retry_and_metrics_zero_safe,
    test_integration_alerts_and_actions_and_integration_audit_logs,
    test_pms_webhook_creates_job_idempotent_and_job_endpoints,
    test_provider_crud_activate_and_audit,
)


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.integrations
@pytest.mark.django_db
def test_be_int_001_provider_crud_activate_deactivate_flow():
    test_provider_crud_activate_and_audit()


@pytest.mark.regression
@pytest.mark.p1
@pytest.mark.integrations
@pytest.mark.django_db
def test_be_int_002_health_and_core_processing_flow():
    test_pms_webhook_creates_job_idempotent_and_job_endpoints()


@pytest.mark.regression
@pytest.mark.p1
@pytest.mark.integrations
@pytest.mark.django_db
def test_be_int_004_005_retry_dead_letter_metrics_flow():
    test_dead_letter_and_manual_retry_and_metrics_zero_safe()


@pytest.mark.regression
@pytest.mark.p2
@pytest.mark.integrations
@pytest.mark.django_db
def test_be_int_007_008_alerts_metrics_audit_consistency():
    test_integration_alerts_and_actions_and_integration_audit_logs()
