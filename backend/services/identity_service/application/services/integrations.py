from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol

from django.db import transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone

from infrastructure.db.core.models import (
    IntegrationJob,
    IntegrationJobAttempt,
    IntegrationProvider,
    Property,
    PurchaseOrder,
    Room,
    RoomStatus,
    Supplier,
    User,
)


class IntegrationError(Exception):
    code = "integration_error"
    retryable = False

    def __init__(self, message: str, *, code: str | None = None, retryable: bool | None = None):
        super().__init__(message)
        if code:
            self.code = code
        if retryable is not None:
            self.retryable = retryable


class MappingError(IntegrationError):
    code = "mapping_error"


class ValidationError(IntegrationError):
    code = "validation_error"


class ProviderTimeoutError(IntegrationError):
    code = "provider_timeout"
    retryable = True


class ProviderServerError(IntegrationError):
    code = "provider_5xx"
    retryable = True


class ProviderClientError(IntegrationError):
    code = "provider_4xx"
    retryable = False


class ProviderAuthError(IntegrationError):
    code = "provider_auth"
    retryable = False


class ConnectorHttpClient(Protocol):
    def request(self, *, method: str, url: str, headers: dict[str, str], payload: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
        ...


class NoopHttpClient:
    def request(self, *, method: str, url: str, headers: dict[str, str], payload: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
        return {"status_code": 200, "body": {"ok": True, "echo": payload}}


@dataclass
class ConnectorResult:
    success: bool
    status_code: int
    body: dict[str, Any]


class ConnectorAdapter:
    def execute(self, *, operation: str, payload: dict[str, Any]) -> ConnectorResult:
        raise NotImplementedError


class BaseHttpConnectorAdapter(ConnectorAdapter):
    def __init__(self, *, provider: IntegrationProvider, http_client: ConnectorHttpClient | None = None) -> None:
        self.provider = provider
        self.http_client = http_client or NoopHttpClient()

    def _auth_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        secret_ref = self.provider.credentials_secret_ref or ""
        if self.provider.auth_type == IntegrationProvider.AUTH_API_KEY:
            headers["X-API-Key"] = secret_ref
        elif self.provider.auth_type == IntegrationProvider.AUTH_BEARER_TOKEN:
            headers["Authorization"] = f"Bearer {secret_ref}"
        elif self.provider.auth_type == IntegrationProvider.AUTH_BASIC:
            headers["Authorization"] = f"Basic {secret_ref}"
        return headers

    def _map_error(self, status_code: int, message: str) -> IntegrationError:
        if status_code == 401:
            return ProviderAuthError(message)
        if status_code == 429 or 500 <= status_code <= 599:
            return ProviderServerError(message)
        if 400 <= status_code <= 499:
            return ProviderClientError(message)
        return IntegrationError(message, retryable=False)

    def execute(self, *, operation: str, payload: dict[str, Any]) -> ConnectorResult:
        if self.provider.status != IntegrationProvider.STATUS_ACTIVE:
            raise ValidationError("Inactive provider cannot execute jobs")

        timeout_seconds = self.provider.timeout_seconds or 15
        endpoint = f"{self.provider.base_url.rstrip('/')}/{operation}"
        try:
            response = self.http_client.request(
                method="POST",
                url=endpoint,
                headers=self._auth_headers(),
                payload=payload,
                timeout_seconds=timeout_seconds,
            )
        except TimeoutError as exc:
            raise ProviderTimeoutError(str(exc)) from exc

        status_code = int(response.get("status_code", 500))
        body = response.get("body", {}) if isinstance(response.get("body"), dict) else {"raw": response.get("body")}

        if status_code >= 400:
            raise self._map_error(status_code, str(body))
        return ConnectorResult(success=True, status_code=status_code, body=body)


class ConnectorAdapterFactory:
    def create(self, provider: IntegrationProvider, *, http_client: ConnectorHttpClient | None = None) -> ConnectorAdapter:
        return BaseHttpConnectorAdapter(provider=provider, http_client=http_client)


class PMSMappingService:
    OCC_MAP = {
        "OCCUPIED": RoomStatus.OCCUPANCY_OCCUPIED,
        "VACANT": RoomStatus.OCCUPANCY_VACANT,
        "RESERVED": RoomStatus.OCCUPANCY_RESERVED,
        "OUT_OF_ORDER": RoomStatus.OCCUPANCY_OUT_OF_ORDER,
    }

    def occupancy_to_command(self, payload: dict[str, Any]) -> dict[str, Any]:
        required = ["property_id", "timestamp"]
        for key in required:
            if key not in payload:
                raise ValidationError(f"Missing field: {key}")

        status_raw = str(payload.get("occupancy_status", "")).upper()
        if status_raw not in self.OCC_MAP:
            raise ValidationError("Invalid occupancy_status")

        room = None
        if payload.get("room_id"):
            room = Room.objects.filter(id=payload["room_id"]).first()
        elif payload.get("room_number"):
            room = Room.objects.filter(property_id=payload["property_id"], room_number=payload["room_number"]).first()
        if not room:
            raise MappingError("Unknown external room mapping")

        return {
            "room_id": room.id,
            "occupancy_status": self.OCC_MAP[status_raw],
            "housekeeping_status": payload.get("housekeeping_status") or RoomStatus.HK_DIRTY,
            "timestamp": payload["timestamp"],
            "guest_id": payload.get("guest_id"),
            "reservation_id": payload.get("reservation_id"),
        }

    def guest_to_command(self, payload: dict[str, Any]) -> dict[str, Any]:
        for key in ["guest_id", "first_name", "last_name", "timestamp"]:
            if key not in payload:
                raise ValidationError(f"Missing field: {key}")
        return {
            "guest_external_id": str(payload["guest_id"]),
            "first_name": payload["first_name"],
            "last_name": payload["last_name"],
            "email": payload.get("email", ""),
            "phone": payload.get("phone", ""),
            "vip_status": bool(payload.get("vip_status", False)),
            "loyalty_number": payload.get("loyalty_number", ""),
            "preferences": payload.get("preferences", {}),
            "timestamp": payload["timestamp"],
        }

    def reservation_to_command(self, payload: dict[str, Any]) -> dict[str, Any]:
        for key in ["reservation_id", "guest_id", "property_id", "check_in_date", "check_out_date", "reservation_status", "timestamp"]:
            if key not in payload:
                raise ValidationError(f"Missing field: {key}")
        room_id = payload.get("room_id")
        if not room_id and payload.get("room_number"):
            room = Room.objects.filter(property_id=payload["property_id"], room_number=payload["room_number"]).first()
            if not room:
                raise MappingError("Unknown external room mapping")
            room_id = room.id
        return {
            "reservation_external_id": str(payload["reservation_id"]),
            "guest_external_id": str(payload["guest_id"]),
            "property_id": payload["property_id"],
            "room_id": room_id,
            "check_in_date": payload["check_in_date"],
            "check_out_date": payload["check_out_date"],
            "reservation_status": str(payload["reservation_status"]).upper(),
            "rate_code": payload.get("rate_code", ""),
            "source": payload.get("source", ""),
            "timestamp": payload["timestamp"],
        }


class AccountingMappingService:
    def supplier_to_external(self, supplier: Supplier) -> dict[str, Any]:
        return {"supplier_code": supplier.supplier_code, "name": supplier.name, "email": supplier.email, "phone": supplier.phone}

    def po_to_external(self, po: PurchaseOrder) -> dict[str, Any]:
        if po.status != PurchaseOrder.STATUS_APPROVED:
            raise ValidationError("Only approved purchase orders can be pushed")
        return {
            "po_number": po.po_number,
            "supplier_code": po.supplier.supplier_code,
            "currency": po.currency,
            "total_amount": float(po.total_amount),
            "requested_date": po.requested_date.isoformat() if po.requested_date else None,
        }


class IoTMappingService:
    def meter_reading_to_command(self, payload: dict[str, Any]) -> dict[str, Any]:
        for key in ["meter_id", "value", "unit", "timestamp"]:
            if key not in payload:
                raise ValidationError(f"Missing field: {key}")
        return {
            "meter_external_id": str(payload["meter_id"]),
            "value": payload["value"],
            "unit": payload["unit"],
            "timestamp": payload["timestamp"],
            "property_id": payload.get("property_id"),
        }


class NotificationMappingService:
    def message_to_provider(self, payload: dict[str, Any]) -> dict[str, Any]:
        for key in ["channel", "recipient", "subject", "body"]:
            if key not in payload:
                raise ValidationError(f"Missing field: {key}")
        channel = str(payload["channel"]).upper()
        if channel not in {"EMAIL", "SMS"}:
            raise ValidationError("Invalid notification channel")
        return {
            "channel": channel,
            "recipient": payload["recipient"],
            "subject": payload["subject"],
            "body": payload["body"],
            "metadata": payload.get("metadata", {}),
        }


class IntegrationProviderService:
    def list(self) -> list[IntegrationProvider]:
        return list(IntegrationProvider.objects.all().order_by("id"))

    def create(self, *, actor: User, data: dict[str, Any]) -> IntegrationProvider:
        return IntegrationProvider.objects.create(created_by=actor, updated_by=actor, **data)

    def update(self, provider: IntegrationProvider, *, actor: User, data: dict[str, Any]) -> IntegrationProvider:
        for key, value in data.items():
            setattr(provider, key, value)
        provider.updated_by = actor
        provider.save()
        return provider

    def health_check(self, provider: IntegrationProvider) -> dict[str, Any]:
        return {
            "provider_id": provider.id,
            "provider_code": provider.provider_code,
            "status": "ok" if provider.status == IntegrationProvider.STATUS_ACTIVE else "inactive",
            "base_url": provider.base_url,
            "checked_at": timezone.now(),
        }


class IntegrationJobService:
    def sanitize(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        masked = {}
        for k, v in payload.items():
            lk = str(k).lower()
            if lk in {"password", "token", "authorization", "api_key", "phone", "email"}:
                masked[k] = "***"
            elif isinstance(v, dict):
                masked[k] = self.sanitize(v)
            else:
                masked[k] = v
        return masked

    def idempotency_key(self, *, provider_code: str, job_type: str, external_event_id: str | None, payload: dict[str, Any], timestamp_value: Any = None) -> str:
        if external_event_id:
            return f"{provider_code}:{job_type}:{external_event_id}"
        digest = hashlib.sha256(f"{provider_code}:{job_type}:{timestamp_value}:{payload}".encode("utf-8")).hexdigest()
        return f"{provider_code}:{job_type}:{digest}"

    @transaction.atomic
    def create_job(
        self,
        *,
        provider: IntegrationProvider,
        job_type: str,
        direction: str,
        idempotency_key: str,
        external_event_id: str = "",
        correlation_id: str = "",
        source_entity_type: str = "",
        source_entity_id: str = "",
        request_payload: dict[str, Any] | None = None,
        max_retries: int | None = None,
    ) -> tuple[IntegrationJob, bool]:
        defaults = {
            "direction": direction,
            "status": IntegrationJob.STATUS_PENDING,
            "external_event_id": external_event_id,
            "correlation_id": correlation_id,
            "source_entity_type": source_entity_type,
            "source_entity_id": source_entity_id,
            "request_payload": self.sanitize(request_payload or {}),
            "max_retries": max_retries if max_retries is not None else int(provider.retry_policy.get("max_retries", 3)),
        }
        job, created = IntegrationJob.objects.get_or_create(
            provider=provider,
            job_type=job_type,
            idempotency_key=idempotency_key,
            defaults=defaults,
        )
        return job, created

    def start(self, job: IntegrationJob) -> IntegrationJob:
        job.status = IntegrationJob.STATUS_RUNNING
        job.started_at = timezone.now()
        job.save(update_fields=["status", "started_at", "updated_at"])
        return job

    def success(self, job: IntegrationJob, response_payload: dict[str, Any]) -> IntegrationJob:
        job.status = IntegrationJob.STATUS_SUCCESS
        job.completed_at = timezone.now()
        job.response_payload = self.sanitize(response_payload)
        job.error_code = ""
        job.error_message = ""
        job.save(update_fields=["status", "completed_at", "response_payload", "error_code", "error_message", "updated_at"])
        return job

    def fail(self, job: IntegrationJob, *, error: IntegrationError, response_payload: dict[str, Any] | None = None) -> IntegrationJob:
        job.status = IntegrationJob.STATUS_FAILED
        job.completed_at = timezone.now()
        job.error_code = error.code
        job.error_message = str(error)
        if response_payload is not None:
            job.response_payload = self.sanitize(response_payload)
        job.save(update_fields=["status", "completed_at", "error_code", "error_message", "response_payload", "updated_at"])
        return job

    def retry(self, job: IntegrationJob, *, next_retry_at: datetime) -> IntegrationJob:
        job.status = IntegrationJob.STATUS_RETRYING
        job.retry_count += 1
        job.next_retry_at = next_retry_at
        job.save(update_fields=["status", "retry_count", "next_retry_at", "updated_at"])
        return job

    def dead_letter(self, job: IntegrationJob) -> IntegrationJob:
        job.status = IntegrationJob.STATUS_DEAD_LETTER
        job.next_retry_at = None
        job.save(update_fields=["status", "next_retry_at", "updated_at"])
        return job


class IntegrationRetryService:
    def compute_next_retry(self, *, retry_count: int, base_seconds: int = 30, max_seconds: int = 3600) -> datetime:
        delay = min(max_seconds, base_seconds * (2 ** max(0, retry_count - 1)))
        jitter = random.randint(0, max(1, delay // 5))
        return timezone.now() + timedelta(seconds=delay + jitter)

    def should_retry(self, error: IntegrationError) -> bool:
        return bool(getattr(error, "retryable", False))

    @transaction.atomic
    def apply_failure(self, *, job: IntegrationJob, error: IntegrationError, job_service: IntegrationJobService) -> IntegrationJob:
        job_service.fail(job, error=error)
        attempt_num = int(job.retry_count) + 1
        IntegrationJobAttempt.objects.create(
            job=job,
            attempt_number=attempt_num,
            status=IntegrationJobAttempt.STATUS_FAILED,
            started_at=job.started_at or timezone.now(),
            completed_at=timezone.now(),
            request_payload=job.request_payload,
            response_payload=job.response_payload,
            error_code=error.code,
            error_message=str(error),
            duration_ms=0,
        )

        if not self.should_retry(error):
            return job
        if job.retry_count >= job.max_retries:
            return job_service.dead_letter(job)
        return job_service.retry(job, next_retry_at=self.compute_next_retry(retry_count=job.retry_count + 1))


class PMSConnectorService:
    def __init__(self) -> None:
        self.mapping = PMSMappingService()
        self.jobs = IntegrationJobService()

    def process_event(self, *, provider: IntegrationProvider, event_type: str, payload: dict[str, Any], external_event_id: str = "", correlation_id: str = "") -> tuple[IntegrationJob, bool]:
        idempotency = self.jobs.idempotency_key(
            provider_code=provider.provider_code,
            job_type=f"PMS_{event_type.upper()}",
            external_event_id=external_event_id,
            payload=payload,
            timestamp_value=payload.get("timestamp"),
        )
        job, created = self.jobs.create_job(
            provider=provider,
            job_type=f"PMS_{event_type.upper()}",
            direction=IntegrationJob.DIRECTION_INBOUND,
            idempotency_key=idempotency,
            external_event_id=external_event_id,
            correlation_id=correlation_id,
            request_payload=payload,
            source_entity_type=event_type,
            source_entity_id=str(external_event_id or ""),
        )
        if not created and job.status == IntegrationJob.STATUS_SUCCESS:
            return job, False

        self.jobs.start(job)
        if event_type == "occupancy":
            cmd = self.mapping.occupancy_to_command(payload)
            room = Room.objects.get(id=cmd["room_id"])
            RoomStatus.objects.update_or_create(
                room=room,
                defaults={
                    "occupancy_status": cmd["occupancy_status"],
                    "housekeeping_status": cmd["housekeeping_status"],
                    "priority": RoomStatus.PRIORITY_MEDIUM,
                },
            )
            self.jobs.success(job, {"room_id": room.id})
        elif event_type == "guests":
            cmd = self.mapping.guest_to_command(payload)
            self.jobs.success(job, {"guest_external_id": cmd["guest_external_id"]})
        elif event_type == "reservations":
            cmd = self.mapping.reservation_to_command(payload)
            self.jobs.success(job, {"reservation_external_id": cmd["reservation_external_id"]})
        else:
            raise ValidationError("Unsupported PMS event type")
        return job, True


class IntegrationHealthService:
    def provider_health(self, provider: IntegrationProvider) -> dict[str, Any]:
        return {
            "provider_id": provider.id,
            "provider_code": provider.provider_code,
            "status": provider.status,
            "provider_type": provider.provider_type,
        }

    def summary(self) -> dict[str, Any]:
        qs = IntegrationJob.objects.all()
        total = qs.count()
        success = qs.filter(status=IntegrationJob.STATUS_SUCCESS).count()
        failed = qs.filter(status=IntegrationJob.STATUS_FAILED).count()
        retrying = qs.filter(status=IntegrationJob.STATUS_RETRYING).count()
        dead = qs.filter(status=IntegrationJob.STATUS_DEAD_LETTER).count()
        avg_ms = (
            IntegrationJobAttempt.objects.filter(completed_at__isnull=False).aggregate(avg=Avg("duration_ms")).get("avg")
            or 0
        )
        failures_by_provider = list(
            qs.filter(status__in=[IntegrationJob.STATUS_FAILED, IntegrationJob.STATUS_DEAD_LETTER])
            .values("provider__provider_code")
            .annotate(count=Count("id"))
            .order_by("provider__provider_code")
        )
        failures_by_job_type = list(
            qs.filter(status__in=[IntegrationJob.STATUS_FAILED, IntegrationJob.STATUS_DEAD_LETTER])
            .values("job_type")
            .annotate(count=Count("id"))
            .order_by("job_type")
        )
        last_success = qs.filter(status=IntegrationJob.STATUS_SUCCESS).order_by("-completed_at").values_list("completed_at", flat=True).first()
        last_failure = qs.filter(status__in=[IntegrationJob.STATUS_FAILED, IntegrationJob.STATUS_DEAD_LETTER]).order_by("-completed_at").values_list("completed_at", flat=True).first()
        return {
            "total_jobs": total,
            "successful_jobs": success,
            "failed_jobs": failed,
            "retrying_jobs": retrying,
            "dead_letter_jobs": dead,
            "average_duration_ms": float(avg_ms or 0),
            "success_rate": float((success / total) * 100) if total else 0.0,
            "failures_by_provider": failures_by_provider,
            "failures_by_job_type": failures_by_job_type,
            "last_success_at": last_success,
            "last_failure_at": last_failure,
        }

    def failures(self) -> dict[str, Any]:
        dead = list(IntegrationJob.objects.filter(status=IntegrationJob.STATUS_DEAD_LETTER).values("id", "provider__provider_code", "job_type", "error_code", "error_message", "retry_count"))
        return {"dead_letter": dead}
