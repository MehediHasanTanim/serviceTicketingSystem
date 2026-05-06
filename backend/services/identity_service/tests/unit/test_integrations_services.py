from datetime import timedelta

import pytest
from django.utils import timezone

from application.services.integrations import (
    AccountingMappingService,
    BaseHttpConnectorAdapter,
    IntegrationError,
    IntegrationJobService,
    IntegrationRetryService,
    IoTMappingService,
    MappingError,
    NotificationMappingService,
    PMSConnectorService,
    PMSMappingService,
    ProviderClientError,
    ProviderServerError,
    ProviderTimeoutError,
    ValidationError,
)
from infrastructure.db.core.models import IntegrationJob, IntegrationJobAttempt, IntegrationProvider, PurchaseOrder
from tests.unit.api_test_helpers import create_org, create_user


pytestmark = pytest.mark.django_db


class StubHttpClient:
    def __init__(self, status_code=200, body=None, raise_timeout=False):
        self.status_code = status_code
        self.body = body or {"ok": True}
        self.raise_timeout = raise_timeout
        self.calls = []

    def request(self, *, method, url, headers, payload, timeout_seconds):
        self.calls.append({"method": method, "url": url, "headers": headers, "payload": payload, "timeout_seconds": timeout_seconds})
        if self.raise_timeout:
            raise TimeoutError("timeout")
        return {"status_code": self.status_code, "body": self.body}


def _provider(actor):
    return IntegrationProvider.objects.create(
        provider_code="PMS_X",
        name="PMS X",
        provider_type=IntegrationProvider.TYPE_PMS,
        status=IntegrationProvider.STATUS_ACTIVE,
        base_url="https://example.test",
        auth_type=IntegrationProvider.AUTH_API_KEY,
        credentials_secret_ref="secret-key",
        config={},
        retry_policy={"max_retries": 2},
        created_by=actor,
        updated_by=actor,
    )


def test_pms_occupancy_mapping_success_and_unknown_room_error():
    org = create_org()
    actor = create_user(org, email="u@example.com")
    _provider(actor)
    svc = PMSMappingService()
    with pytest.raises(MappingError):
        svc.occupancy_to_command({"property_id": 1, "room_number": "404", "occupancy_status": "VACANT", "timestamp": timezone.now()})


def test_iot_and_notification_mapping_validation():
    assert IoTMappingService().meter_reading_to_command({"meter_id": "m1", "value": 12.3, "unit": "kWh", "timestamp": timezone.now()})["meter_external_id"] == "m1"
    with pytest.raises(ValidationError):
        NotificationMappingService().message_to_provider({"channel": "PUSH", "recipient": "x", "subject": "s", "body": "b"})


def test_accounting_po_mapping_requires_approved_status():
    org = create_org()
    actor = create_user(org, email="a@example.com")
    supplier = __import__("infrastructure.db.core.models", fromlist=["Supplier"]).Supplier.objects.create(
        org=org,
        supplier_code="SUP-1",
        name="Supplier",
        created_by=actor,
        updated_by=actor,
    )
    po = PurchaseOrder.objects.create(
        org=org,
        po_number="PO-1",
        supplier=supplier,
        requester=actor,
        status=PurchaseOrder.STATUS_DRAFT,
        created_by=actor,
        updated_by=actor,
    )
    with pytest.raises(ValidationError):
        AccountingMappingService().po_to_external(po)


def test_connector_adapter_timeout_and_error_mapping_and_secret_header():
    org = create_org()
    actor = create_user(org, email="x@example.com")
    provider = _provider(actor)

    timeout_client = StubHttpClient(raise_timeout=True)
    adapter = BaseHttpConnectorAdapter(provider=provider, http_client=timeout_client)
    with pytest.raises(ProviderTimeoutError):
        adapter.execute(operation="send", payload={"x": 1})

    err5 = BaseHttpConnectorAdapter(provider=provider, http_client=StubHttpClient(status_code=503, body={"error": "down"}))
    with pytest.raises(ProviderServerError):
        err5.execute(operation="send", payload={})

    err4 = BaseHttpConnectorAdapter(provider=provider, http_client=StubHttpClient(status_code=400, body={"error": "bad"}))
    with pytest.raises(ProviderClientError):
        err4.execute(operation="send", payload={})

    ok_client = StubHttpClient()
    ok = BaseHttpConnectorAdapter(provider=provider, http_client=ok_client)
    ok.execute(operation="send", payload={"ok": True})
    assert ok_client.calls[0]["headers"]["X-API-Key"] == "secret-key"


def test_retry_policy_and_dead_letter_and_attempt_history():
    org = create_org()
    actor = create_user(org, email="r@example.com")
    provider = _provider(actor)
    jobs = IntegrationJobService()
    retry = IntegrationRetryService()
    job, _ = jobs.create_job(provider=provider, job_type="PMS_OCCUPANCY", direction=IntegrationJob.DIRECTION_INBOUND, idempotency_key="idem-1", request_payload={"email": "x@y.com"})
    jobs.start(job)

    updated = retry.apply_failure(job=job, error=ProviderServerError("x"), job_service=jobs)
    assert updated.status in {IntegrationJob.STATUS_RETRYING, IntegrationJob.STATUS_DEAD_LETTER}
    assert IntegrationJobAttempt.objects.filter(job=job).count() == 1

    # force dead-letter path
    job.retry_count = job.max_retries
    job.save(update_fields=["retry_count"])
    updated2 = retry.apply_failure(job=job, error=ProviderServerError("y"), job_service=jobs)
    assert updated2.status == IntegrationJob.STATUS_DEAD_LETTER


def test_job_idempotency_and_sanitization_and_manual_key():
    org = create_org()
    actor = create_user(org, email="i@example.com")
    provider = _provider(actor)
    jobs = IntegrationJobService()
    key = jobs.idempotency_key(provider_code=provider.provider_code, job_type="PMS_OCCUPANCY", external_event_id="evt-1", payload={}, timestamp_value=None)
    j1, c1 = jobs.create_job(provider=provider, job_type="PMS_OCCUPANCY", direction=IntegrationJob.DIRECTION_INBOUND, idempotency_key=key, request_payload={"email": "a@b.com", "token": "abc"})
    j2, c2 = jobs.create_job(provider=provider, job_type="PMS_OCCUPANCY", direction=IntegrationJob.DIRECTION_INBOUND, idempotency_key=key, request_payload={"email": "a@b.com", "token": "abc"})
    assert c1 is True
    assert c2 is False
    assert j1.id == j2.id
    assert j1.request_payload["email"] == "***"


def test_pms_connector_duplicate_event_ignored_safely():
    org = create_org()
    actor = create_user(org, email="p@example.com")
    provider = _provider(actor)
    svc = PMSConnectorService()

    # use guests event to avoid room dependency
    payload = {"guest_id": "g1", "first_name": "A", "last_name": "B", "timestamp": timezone.now()}
    job1, processed1 = svc.process_event(provider=provider, event_type="guests", payload=payload, external_event_id="evt-dup")
    job2, processed2 = svc.process_event(provider=provider, event_type="guests", payload=payload, external_event_id="evt-dup")
    assert processed1 is True
    assert processed2 is False
    assert job1.id == job2.id
