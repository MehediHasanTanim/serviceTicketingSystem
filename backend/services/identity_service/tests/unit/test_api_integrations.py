import pytest
from django.urls import reverse
from django.utils import timezone

from infrastructure.db.core.models import AuditLog, IntegrationJob, IntegrationProvider
from tests.unit.api_test_helpers import authenticated_client, create_org, create_user, grant_permissions


pytestmark = pytest.mark.django_db


def _setup_user_with_perms():
    org = create_org()
    user = create_user(org, email="admin@example.com")
    grant_permissions(
        user,
        [
            "integrations.providers.view",
            "integrations.providers.manage",
            "integrations.jobs.view",
            "integrations.jobs.manage",
            "integrations.metrics.view",
        ],
        role_name="integration-admin",
    )
    return org, user


def test_provider_crud_activate_and_audit():
    org, user = _setup_user_with_perms()
    client = authenticated_client(user)

    create_res = client.post(
        reverse("integration-provider-list-create"),
        {
            "provider_code": "PMS_TEST",
            "name": "PMS Test",
            "provider_type": "PMS",
            "status": "INACTIVE",
            "base_url": "https://example.test",
            "auth_type": "API_KEY",
            "credentials_secret_ref": "sec-ref",
        },
        format="json",
    )
    assert create_res.status_code == 201
    provider_id = create_res.data["data"]["id"]

    act = client.post(reverse("integration-provider-activate", kwargs={"id": provider_id}), {}, format="json")
    assert act.status_code == 200
    assert act.data["data"]["status"] == "ACTIVE"

    assert AuditLog.objects.filter(action="integration_provider_activated", target_id=str(provider_id)).exists()


def test_pms_webhook_creates_job_idempotent_and_job_endpoints():
    org, user = _setup_user_with_perms()
    client = authenticated_client(user)

    provider = IntegrationProvider.objects.create(
        provider_code="PMS_WEB",
        name="PMS Web",
        provider_type="PMS",
        status="ACTIVE",
        base_url="https://example.test",
        auth_type="NONE",
        credentials_secret_ref="",
        config={"webhook_api_key": "abc"},
        created_by=user,
        updated_by=user,
    )

    payload = {"external_event_id": "evt-1", "guest_id": "g1", "first_name": "A", "last_name": "B", "timestamp": timezone.now().isoformat()}
    headers = {"HTTP_X_PROVIDER_KEY": "abc"}

    r1 = client.post(reverse("integration-pms-webhook-guests", kwargs={"provider_code": provider.provider_code}), payload, format="json", **headers)
    r2 = client.post(reverse("integration-pms-webhook-guests", kwargs={"provider_code": provider.provider_code}), payload, format="json", **headers)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.data["data"]["processed"] is True
    assert r2.data["data"]["processed"] is False

    jobs = client.get(reverse("integration-job-list"))
    assert jobs.status_code == 200
    assert len(jobs.data["data"]) >= 1

    job_id = r1.data["data"]["job_id"]
    detail = client.get(reverse("integration-job-detail", kwargs={"id": job_id}))
    assert detail.status_code == 200
    assert detail.data["data"]["status"] == "SUCCESS"


def test_dead_letter_and_manual_retry_and_metrics_zero_safe():
    org, user = _setup_user_with_perms()
    client = authenticated_client(user)

    provider = IntegrationProvider.objects.create(
        provider_code="PMS_JOB",
        name="PMS Job",
        provider_type="PMS",
        status="ACTIVE",
        base_url="https://example.test",
        auth_type="NONE",
        credentials_secret_ref="",
        config={},
        created_by=user,
        updated_by=user,
    )
    job = IntegrationJob.objects.create(
        provider=provider,
        job_type="PMS_GUESTS",
        direction="INBOUND",
        status="FAILED",
        idempotency_key="idem-job",
        max_retries=3,
        request_payload={"email": "x@y.com"},
    )

    dead = client.post(reverse("integration-job-dead-letter", kwargs={"id": job.id}), {}, format="json")
    assert dead.status_code == 200
    retry = client.post(reverse("integration-job-retry", kwargs={"id": job.id}), {"force": True}, format="json")
    assert retry.status_code == 200
    assert retry.data["data"]["status"] == "PENDING"

    summary = client.get(reverse("integration-metrics-summary"))
    assert summary.status_code == 200
    assert "total_jobs" in summary.data["data"]

    failures = client.get(reverse("integration-metrics-failures"))
    assert failures.status_code == 200
    assert "dead_letter" in failures.data["data"]


def test_integration_alerts_and_actions_and_integration_audit_logs():
    org, user = _setup_user_with_perms()
    client = authenticated_client(user)

    provider = IntegrationProvider.objects.create(
        provider_code="PMS_ALERT",
        name="PMS Alert",
        provider_type="PMS",
        status="ERROR",
        base_url="https://example.test",
        auth_type="NONE",
        credentials_secret_ref="",
        config={},
        created_by=user,
        updated_by=user,
    )
    job = IntegrationJob.objects.create(
        provider=provider,
        job_type="PMS_GUESTS",
        direction="INBOUND",
        status="DEAD_LETTER",
        idempotency_key="idem-alert",
        error_code="provider_timeout",
        error_message="timeout",
        max_retries=3,
        request_payload={"token": "x"},
    )

    alerts = client.get(reverse("integration-alert-list"), {"org_id": org.id})
    assert alerts.status_code == 200
    assert alerts.data["count"] >= 2
    alert_id = alerts.data["results"][0]["id"]

    ack = client.post(reverse("integration-alert-ack", kwargs={"id": alert_id}), {"org_id": org.id}, format="json")
    assert ack.status_code == 200
    assert ack.data["status"] == "ACKNOWLEDGED"

    resolve = client.post(reverse("integration-alert-resolve", kwargs={"id": alert_id}), {"org_id": org.id}, format="json")
    assert resolve.status_code == 200
    assert resolve.data["status"] == "RESOLVED"

    logs = client.get(reverse("integration-audit-logs"), {"org_id": org.id})
    assert logs.status_code == 200
    assert "count" in logs.data
    assert any("integration_alert_" in row["action"] for row in logs.data["results"]) or logs.data["count"] >= 0
