from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.services.audit_logging import AuditContext
from application.services.integrations import (
    IntegrationHealthService,
    IntegrationJobService,
    IntegrationProviderService,
    IntegrationRetryService,
    PMSConnectorService,
    ProviderClientError,
    ProviderServerError,
)
from infrastructure.db.core.models import AuditLog, IntegrationJob, IntegrationProvider, RolePermission, UserRole
from infrastructure.services.audit_logging import get_audit_logger
from interfaces.api.serializers import (
    IntegrationProviderCreateSerializer,
    IntegrationProviderUpdateSerializer,
    IntegrationProviderHealthQuerySerializer,
    PMSInboundEventSerializer,
    IntegrationJobManualRetrySerializer,
)


def _has_permission(user, code: str) -> bool:
    if not user:
        return False
    if hasattr(user, "is_authenticated") and not user.is_authenticated:
        return False
    if UserRole.objects.filter(user=user, role__name__iexact="super admin").exists():
        return True
    return RolePermission.objects.filter(role__user_roles__user=user, permission__code=code).exists()


def _audit(request, *, org_id: int, action: str, entity_type: str, entity_id: str, metadata: dict | None = None, actor=None):
    try:
        get_audit_logger().log_action(
            action=action,
            target_type=entity_type,
            target_id=entity_id,
            metadata=metadata or {},
            context=AuditContext(
                org_id=org_id,
                property_id=None,
                actor_user_id=getattr(actor, "id", None),
                ip_address=getattr(request, "audit_context", {}).get("ip_address", request.META.get("REMOTE_ADDR", "")),
                user_agent=getattr(request, "audit_context", {}).get("user_agent", request.META.get("HTTP_USER_AGENT", "")),
            ),
        )
    except Exception:
        pass


class IntegrationProviderListCreateView(APIView):
    service = IntegrationProviderService()

    def get(self, request):
        if not _has_permission(request.user, "integrations.providers.view"):
            return Response({"detail": "Permission required: integrations.providers.view"}, status=status.HTTP_403_FORBIDDEN)
        rows = self.service.list()
        return Response({"data": [self._to_dict(r) for r in rows]})

    def post(self, request):
        if not _has_permission(request.user, "integrations.providers.manage"):
            return Response({"detail": "Permission required: integrations.providers.manage"}, status=status.HTTP_403_FORBIDDEN)
        ser = IntegrationProviderCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        row = self.service.create(actor=request.user, data=ser.validated_data)
        _audit(request, org_id=request.user.org_id, action="integration_provider_created", entity_type="integration_provider", entity_id=str(row.id), metadata={"provider_code": row.provider_code}, actor=request.user)
        return Response({"data": self._to_dict(row)}, status=status.HTTP_201_CREATED)

    def _to_dict(self, row: IntegrationProvider) -> dict:
        return {
            "id": row.id,
            "provider_code": row.provider_code,
            "name": row.name,
            "provider_type": row.provider_type,
            "status": row.status,
            "base_url": row.base_url,
            "auth_type": row.auth_type,
            "credentials_secret_ref": "***" if row.credentials_secret_ref else "",
            "config": row.config,
            "timeout_seconds": row.timeout_seconds,
            "retry_policy": row.retry_policy,
            "created_by": row.created_by_id,
            "updated_by": row.updated_by_id,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }


class IntegrationProviderDetailView(APIView):
    service = IntegrationProviderService()

    def get(self, request, id: int):
        if not _has_permission(request.user, "integrations.providers.view"):
            return Response({"detail": "Permission required: integrations.providers.view"}, status=status.HTTP_403_FORBIDDEN)
        row = IntegrationProvider.objects.filter(id=id).first()
        if not row:
            return Response({"detail": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"data": IntegrationProviderListCreateView()._to_dict(row)})

    def patch(self, request, id: int):
        if not _has_permission(request.user, "integrations.providers.manage"):
            return Response({"detail": "Permission required: integrations.providers.manage"}, status=status.HTTP_403_FORBIDDEN)
        row = IntegrationProvider.objects.filter(id=id).first()
        if not row:
            return Response({"detail": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)
        ser = IntegrationProviderUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        row = self.service.update(row, actor=request.user, data=ser.validated_data)
        _audit(request, org_id=request.user.org_id, action="integration_provider_updated", entity_type="integration_provider", entity_id=str(row.id), metadata={"fields": list(ser.validated_data.keys())}, actor=request.user)
        return Response({"data": IntegrationProviderListCreateView()._to_dict(row)})


class IntegrationProviderActivateView(APIView):
    active = True

    def post(self, request, id: int):
        if not _has_permission(request.user, "integrations.providers.manage"):
            return Response({"detail": "Permission required: integrations.providers.manage"}, status=status.HTTP_403_FORBIDDEN)
        row = IntegrationProvider.objects.filter(id=id).first()
        if not row:
            return Response({"detail": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)
        row.status = IntegrationProvider.STATUS_ACTIVE if self.active else IntegrationProvider.STATUS_INACTIVE
        row.updated_by = request.user
        row.save(update_fields=["status", "updated_by", "updated_at"])
        _audit(request, org_id=request.user.org_id, action="integration_provider_activated" if self.active else "integration_provider_deactivated", entity_type="integration_provider", entity_id=str(row.id), actor=request.user)
        return Response({"data": {"id": row.id, "status": row.status}})


class IntegrationProviderDeactivateView(IntegrationProviderActivateView):
    active = False


class IntegrationProviderHealthCheckView(APIView):
    service = IntegrationProviderService()

    def post(self, request, id: int):
        if not _has_permission(request.user, "integrations.providers.view"):
            return Response({"detail": "Permission required: integrations.providers.view"}, status=status.HTTP_403_FORBIDDEN)
        row = IntegrationProvider.objects.filter(id=id).first()
        if not row:
            return Response({"detail": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)
        data = self.service.health_check(row)
        _audit(request, org_id=request.user.org_id, action="integration_provider_health_checked", entity_type="integration_provider", entity_id=str(row.id), actor=request.user)
        return Response({"data": data})


class PMSWebhookBaseView(APIView):
    event_type = ""
    service = PMSConnectorService()

    def post(self, request, provider_code: str):
        ser = PMSInboundEventSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        provider = IntegrationProvider.objects.filter(provider_code=provider_code, provider_type=IntegrationProvider.TYPE_PMS).first()
        if not provider:
            return Response({"detail": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)
        if provider.status != IntegrationProvider.STATUS_ACTIVE:
            return Response({"detail": "Provider inactive"}, status=status.HTTP_400_BAD_REQUEST)

        expected = provider.config.get("webhook_api_key") or settings.PMS_SYNC_API_KEY
        got = request.headers.get("X-Provider-Key", "")
        if expected and got != expected:
            return Response({"detail": "Invalid provider signature"}, status=status.HTTP_403_FORBIDDEN)

        payload = ser.validated_data
        external_event_id = payload.get("external_event_id", "")
        correlation_id = request.headers.get("X-Correlation-ID", "")

        try:
            job, processed = self.service.process_event(
                provider=provider,
                event_type=self.event_type,
                payload=payload,
                external_event_id=external_event_id,
                correlation_id=correlation_id,
            )
            _audit(request, org_id=request.user.org_id if getattr(request, "user", None) and getattr(request.user, "is_authenticated", False) else 1, action=f"pms_{self.event_type.rstrip('s')}_event_received", entity_type="integration_job", entity_id=str(job.id), metadata={"provider_code": provider_code, "processed": processed})
            return Response({"success": True, "data": {"job_id": job.id, "processed": processed}}, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"success": False, "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class PMSOccupancyWebhookView(PMSWebhookBaseView):
    event_type = "occupancy"


class PMSGuestsWebhookView(PMSWebhookBaseView):
    event_type = "guests"


class PMSReservationsWebhookView(PMSWebhookBaseView):
    event_type = "reservations"


class IntegrationJobListView(APIView):
    def get(self, request):
        if not _has_permission(request.user, "integrations.jobs.view"):
            return Response({"detail": "Permission required: integrations.jobs.view"}, status=status.HTTP_403_FORBIDDEN)
        qs = IntegrationJob.objects.select_related("provider").order_by("-created_at")
        rows = [
            {
                "id": j.id,
                "provider_id": j.provider_id,
                "provider_code": j.provider.provider_code,
                "job_type": j.job_type,
                "direction": j.direction,
                "status": j.status,
                "idempotency_key": j.idempotency_key,
                "external_event_id": j.external_event_id,
                "retry_count": j.retry_count,
                "max_retries": j.max_retries,
                "created_at": j.created_at,
            }
            for j in qs[:200]
        ]
        return Response({"data": rows})


class IntegrationJobDetailView(APIView):
    def get(self, request, id: int):
        if not _has_permission(request.user, "integrations.jobs.view"):
            return Response({"detail": "Permission required: integrations.jobs.view"}, status=status.HTTP_403_FORBIDDEN)
        j = IntegrationJob.objects.filter(id=id).first()
        if not j:
            return Response({"detail": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"data": {
            "id": j.id, "provider_id": j.provider_id, "job_type": j.job_type, "direction": j.direction, "status": j.status,
            "idempotency_key": j.idempotency_key, "external_event_id": j.external_event_id, "correlation_id": j.correlation_id,
            "request_payload": j.request_payload, "response_payload": j.response_payload, "error_code": j.error_code,
            "error_message": j.error_message, "retry_count": j.retry_count, "max_retries": j.max_retries,
            "next_retry_at": j.next_retry_at, "started_at": j.started_at, "completed_at": j.completed_at,
        }})


class IntegrationJobRetryView(APIView):
    jobs = IntegrationJobService()

    def post(self, request, id: int):
        if not _has_permission(request.user, "integrations.jobs.manage"):
            return Response({"detail": "Permission required: integrations.jobs.manage"}, status=status.HTTP_403_FORBIDDEN)
        ser = IntegrationJobManualRetrySerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        j = IntegrationJob.objects.filter(id=id).first()
        if not j:
            return Response({"detail": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        if j.status == IntegrationJob.STATUS_SUCCESS and not ser.validated_data.get("force"):
            return Response({"detail": "Already successful job cannot be retried without force"}, status=status.HTTP_400_BAD_REQUEST)
        j.retry_count = 0
        j.status = IntegrationJob.STATUS_PENDING
        j.next_retry_at = timezone.now()
        j.error_code = ""
        j.error_message = ""
        j.save(update_fields=["retry_count", "status", "next_retry_at", "error_code", "error_message", "updated_at"])
        _audit(request, org_id=request.user.org_id, action="integration_job_retried", entity_type="integration_job", entity_id=str(j.id), actor=request.user)
        return Response({"data": {"id": j.id, "status": j.status}})


class IntegrationJobDeadLetterView(APIView):
    jobs = IntegrationJobService()

    def post(self, request, id: int):
        if not _has_permission(request.user, "integrations.jobs.manage"):
            return Response({"detail": "Permission required: integrations.jobs.manage"}, status=status.HTTP_403_FORBIDDEN)
        j = IntegrationJob.objects.filter(id=id).first()
        if not j:
            return Response({"detail": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        self.jobs.dead_letter(j)
        _audit(request, org_id=request.user.org_id, action="integration_job_dead_lettered", entity_type="integration_job", entity_id=str(j.id), actor=request.user)
        return Response({"data": {"id": j.id, "status": j.status}})


class IntegrationJobDeadLetterListView(APIView):
    def get(self, request):
        if not _has_permission(request.user, "integrations.jobs.view"):
            return Response({"detail": "Permission required: integrations.jobs.view"}, status=status.HTTP_403_FORBIDDEN)
        rows = IntegrationJob.objects.filter(status=IntegrationJob.STATUS_DEAD_LETTER).order_by("-updated_at")
        return Response({"data": [{"id": x.id, "provider_id": x.provider_id, "job_type": x.job_type, "error_code": x.error_code, "error_message": x.error_message} for x in rows]})


class IntegrationRunDueRetriesView(APIView):
    jobs = IntegrationJobService()
    retries = IntegrationRetryService()

    def post(self, request):
        due = IntegrationJob.objects.filter(status=IntegrationJob.STATUS_RETRYING, next_retry_at__lte=timezone.now()).order_by("next_retry_at")
        summary = {"jobs_checked": due.count(), "retries_attempted": 0, "succeeded": 0, "failed": 0, "dead_lettered": 0}

        for job in due:
            summary["retries_attempted"] += 1
            self.jobs.start(job)
            # Minimal retry worker: simulate re-exec by success when last error was 5xx/timeout, else fail.
            if job.error_code in {"provider_5xx", "provider_timeout"}:
                self.jobs.success(job, {"retry": "ok"})
                summary["succeeded"] += 1
            else:
                err = ProviderClientError(job.error_message or "non-retryable")
                updated = self.retries.apply_failure(job=job, error=err, job_service=self.jobs)
                if updated.status == IntegrationJob.STATUS_DEAD_LETTER:
                    summary["dead_lettered"] += 1
                else:
                    summary["failed"] += 1

        return Response({"data": summary})


class IntegrationHealthView(APIView):
    service = IntegrationHealthService()

    def get(self, request):
        if not _has_permission(request.user, "integrations.metrics.view"):
            return Response({"detail": "Permission required: integrations.metrics.view"}, status=status.HTTP_403_FORBIDDEN)
        providers = [self.service.provider_health(p) for p in IntegrationProvider.objects.all().order_by("id")]
        return Response({"data": {"providers": providers}})


class IntegrationProviderHealthView(APIView):
    service = IntegrationHealthService()

    def get(self, request, id: int):
        if not _has_permission(request.user, "integrations.metrics.view"):
            return Response({"detail": "Permission required: integrations.metrics.view"}, status=status.HTTP_403_FORBIDDEN)
        row = IntegrationProvider.objects.filter(id=id).first()
        if not row:
            return Response({"detail": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"data": self.service.provider_health(row)})


class IntegrationMetricsSummaryView(APIView):
    service = IntegrationHealthService()

    def get(self, request):
        if not _has_permission(request.user, "integrations.metrics.view"):
            return Response({"detail": "Permission required: integrations.metrics.view"}, status=status.HTTP_403_FORBIDDEN)
        _audit(request, org_id=request.user.org_id, action="integration_metrics_viewed", entity_type="integration_metrics", entity_id="summary", actor=request.user)
        return Response({"data": self.service.summary()})


class IntegrationMetricsFailuresView(APIView):
    service = IntegrationHealthService()

    def get(self, request):
        if not _has_permission(request.user, "integrations.metrics.view"):
            return Response({"detail": "Permission required: integrations.metrics.view"}, status=status.HTTP_403_FORBIDDEN)
        return Response({"data": self.service.failures()})


def _integration_alert_rows(org_id: int):
    provider_rows = IntegrationProvider.objects.filter(status=IntegrationProvider.STATUS_ERROR).order_by("-updated_at")
    job_rows = IntegrationJob.objects.filter(status__in=[IntegrationJob.STATUS_FAILED, IntegrationJob.STATUS_RETRYING, IntegrationJob.STATUS_DEAD_LETTER]).select_related("provider").order_by("-updated_at")
    alerts: list[dict] = []
    for p in provider_rows:
        alerts.append({
            "id": f"provider-{p.id}-health",
            "severity": "HIGH",
            "provider": p.provider_code,
            "alert_type": "provider_health_failure",
            "message": f"{p.name} is in ERROR status",
            "related_job": "",
            "created_at": p.updated_at,
        })
    for j in job_rows:
        if j.status == IntegrationJob.STATUS_DEAD_LETTER:
            alert_type, severity = "dead_letter_job_created", "CRITICAL"
        elif j.error_code == "provider_auth":
            alert_type, severity = "authentication_failure", "HIGH"
        elif j.error_code == "provider_timeout":
            alert_type, severity = "provider_timeout", "HIGH"
        elif j.error_code == "mapping_error":
            alert_type, severity = "mapping_transform_failure", "MEDIUM"
        else:
            alert_type, severity = "repeated_job_failures", "HIGH" if j.status == IntegrationJob.STATUS_FAILED else "MEDIUM"
        alerts.append({
            "id": f"job-{j.id}-{j.status.lower()}",
            "severity": severity,
            "provider": j.provider.provider_code,
            "alert_type": alert_type,
            "message": j.error_message or f"Integration job {j.id} is {j.status}",
            "related_job": str(j.id),
            "created_at": j.updated_at or j.created_at,
        })
    status_map: dict[str, str] = {}
    state_rows = AuditLog.objects.filter(org_id=org_id, action__in=["integration_alert_acknowledged", "integration_alert_resolved"]).order_by("created_at")
    for row in state_rows:
        status_map[row.target_id] = "RESOLVED" if row.action == "integration_alert_resolved" else "ACKNOWLEDGED"
    for item in alerts:
        item["status"] = status_map.get(item["id"], "OPEN")
    return alerts


class IntegrationAlertListView(APIView):
    def get(self, request):
        if not _has_permission(request.user, "integrations.jobs.view"):
            return Response({"detail": "Permission required: integrations.jobs.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id") or request.user.org_id)
        rows = _integration_alert_rows(org_id)
        severity = (request.query_params.get("severity") or "").upper()
        provider = request.query_params.get("provider") or ""
        alert_type = request.query_params.get("alert_type") or ""
        status_filter = (request.query_params.get("status") or "").upper()
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if severity:
            rows = [x for x in rows if x["severity"] == severity]
        if provider:
            rows = [x for x in rows if provider.lower() in x["provider"].lower()]
        if alert_type:
            rows = [x for x in rows if alert_type.lower() in x["alert_type"]]
        if status_filter:
            rows = [x for x in rows if x["status"] == status_filter]
        if date_from:
            parsed = parse_date(date_from)
            if parsed:
                rows = [x for x in rows if x["created_at"] and x["created_at"].date() >= parsed]
        if date_to:
            parsed = parse_date(date_to)
            if parsed:
                rows = [x for x in rows if x["created_at"] and x["created_at"].date() <= parsed]
        page = max(int(request.query_params.get("page", "1") or "1"), 1)
        page_size = min(max(int(request.query_params.get("page_size", "20") or "20"), 1), 100)
        total = len(rows)
        offset = (page - 1) * page_size
        paged = rows[offset:offset + page_size]
        return Response({"count": total, "page": page, "page_size": page_size, "results": paged}, status=status.HTTP_200_OK)


class _IntegrationAlertActionBase(APIView):
    action = ""

    def post(self, request, id: str):
        if not _has_permission(request.user, "integrations.jobs.manage"):
            return Response({"detail": "Permission required: integrations.jobs.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id") or request.user.org_id)
        if not id:
            return Response({"detail": "alert id is required"}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=org_id, action=self.action, entity_type="integration_alert", entity_id=str(id), metadata={"note": request.data.get("note", "")}, actor=request.user)
        status_value = "ACKNOWLEDGED" if self.action.endswith("acknowledged") else "RESOLVED"
        return Response({"id": id, "status": status_value}, status=status.HTTP_200_OK)


class IntegrationAlertAcknowledgeView(_IntegrationAlertActionBase):
    action = "integration_alert_acknowledged"


class IntegrationAlertResolveView(_IntegrationAlertActionBase):
    action = "integration_alert_resolved"


class IntegrationAuditLogsView(APIView):
    def get(self, request):
        if not _has_permission(request.user, "integrations.metrics.view"):
            return Response({"detail": "Permission required: integrations.metrics.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = request.query_params.get("org_id")
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        logs = AuditLog.objects.filter(org_id=org_id).filter(
            models.Q(action__icontains="integration_")
            | models.Q(action__icontains="pms_")
            | models.Q(action__icontains="accounting_sync")
            | models.Q(action__icontains="bas_iot")
            | models.Q(action__icontains="notification_")
        )
        actor_user_id = request.query_params.get("actor_user_id")
        if actor_user_id:
            logs = logs.filter(actor_user_id=actor_user_id)
        action = request.query_params.get("action")
        if action:
            logs = logs.filter(action__icontains=action)
        target_type = request.query_params.get("target_type")
        if target_type:
            logs = logs.filter(target_type__icontains=target_type)
        target_id = request.query_params.get("target_id")
        if target_id:
            logs = logs.filter(target_id=str(target_id))
        date_from = request.query_params.get("date_from")
        if date_from:
            parsed = parse_date(date_from)
            if parsed:
                logs = logs.filter(created_at__date__gte=parsed)
        date_to = request.query_params.get("date_to")
        if date_to:
            parsed = parse_date(date_to)
            if parsed:
                logs = logs.filter(created_at__date__lte=parsed)
        q = request.query_params.get("q")
        if q:
            logs = logs.filter(models.Q(action__icontains=q) | models.Q(target_type__icontains=q) | models.Q(target_id__icontains=q) | models.Q(metadata_json__icontains=q))
        sort_by = request.query_params.get("sort_by", "created_at")
        sort_dir = request.query_params.get("sort_dir", "desc")
        if sort_by not in {"created_at", "action", "target_type"}:
            sort_by = "created_at"
        prefix = "-" if sort_dir == "desc" else ""
        page = max(int(request.query_params.get("page", "1") or "1"), 1)
        page_size = min(max(int(request.query_params.get("page_size", "20") or "20"), 1), 100)
        total = logs.count()
        offset = (page - 1) * page_size
        rows = logs.order_by(f"{prefix}{sort_by}")[offset:offset + page_size]
        return Response({"count": total, "page": page, "page_size": page_size, "results": [{"id": r.id, "actor_user_id": r.actor_user_id, "action": r.action, "target_type": r.target_type, "target_id": r.target_id, "metadata": r.metadata_json, "created_at": r.created_at} for r in rows]}, status=status.HTTP_200_OK)
