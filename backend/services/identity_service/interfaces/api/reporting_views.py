from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from application.services.audit_logging import AuditContext
from application.services.reporting import (
    CrossModuleAnalyticsService,
    DataMartPipelineService,
    OperationalMetricSnapshotRepository,
    ReportDefinitionRepository,
    ReportDefinitionService,
    ReportGenerationService,
    ReportRunRepository,
    ReportScheduleRepository,
    ReportSchedulerService,
    ReportingFilters,
    ReportingNotFoundError,
    ReportingValidationError,
)
from infrastructure.db.core.models import RolePermission, UserRole
from infrastructure.services.audit_logging import get_audit_logger
from interfaces.api.serializers import (
    DataMartRefreshSerializer,
    ReportDefinitionCreateSerializer,
    ReportDefinitionUpdateSerializer,
    ReportRunRequestSerializer,
    ReportScheduleCreateSerializer,
    ReportScheduleUpdateSerializer,
    ReportingMetricFilterSerializer,
)


def _has_permission(user, code: str) -> bool:
    if not user or (hasattr(user, "is_authenticated") and not user.is_authenticated):
        return False
    if UserRole.objects.filter(user=user, role__name__iexact="super admin").exists():
        return True
    return RolePermission.objects.filter(role__user_roles__user=user, permission__code=code).exists()


def _audit(request, *, org_id: int, action: str, target_type: str, target_id: str, metadata=None, actor=None):
    try:
        meta = getattr(request, "audit_context", {})
        get_audit_logger().log_action(
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata or {},
            context=AuditContext(
                org_id=org_id,
                property_id=None,
                actor_user_id=getattr(actor, "id", None),
                ip_address=meta.get("ip_address", request.META.get("REMOTE_ADDR", "")),
                user_agent=meta.get("user_agent", request.META.get("HTTP_USER_AGENT", "")),
            ),
        )
    except Exception:
        pass


class DataMartRefreshView(APIView):
    service = DataMartPipelineService()

    @extend_schema(request=DataMartRefreshSerializer)
    def post(self, request):
        if not _has_permission(request.user, "reporting.data_mart.refresh"):
            return Response({"detail": "Permission required: reporting.data_mart.refresh"}, status=status.HTTP_403_FORBIDDEN)
        ser = DataMartRefreshSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        _audit(request, org_id=getattr(request.user, "org_id", 0), action="data_mart_refresh_started", target_type="reporting", target_id="data_mart", metadata=data, actor=request.user)
        run = self.service.refresh(period_start=data["period_start"], period_end=data["period_end"], run_type=data["run_type"], triggered_by=request.user)
        _audit(
            request,
            org_id=getattr(request.user, "org_id", 0),
            action="data_mart_refresh_completed" if run.status == "COMPLETED" else "data_mart_refresh_failed",
            target_type="report_data_mart_run",
            target_id=str(run.id),
            metadata={"status": run.status, "errors": run.errors},
            actor=request.user,
        )
        return Response({"id": run.id, "status": run.status, "modules_processed": run.modules_processed, "records_processed": run.records_processed, "errors": run.errors}, status=status.HTTP_200_OK)


class DataMartRunsView(APIView):
    repository = ReportScheduleRepository()

    def get(self, request):
        if not _has_permission(request.user, "reporting.data_mart.view"):
            return Response({"detail": "Permission required: reporting.data_mart.view"}, status=status.HTTP_403_FORBIDDEN)
        from infrastructure.db.core.models import ReportDataMartRun

        rows = ReportDataMartRun.objects.order_by("-created_at")[:100]
        return Response({"count": rows.count(), "results": [{"id": r.id, "status": r.status, "run_type": r.run_type, "period_start": r.period_start, "period_end": r.period_end, "records_processed": r.records_processed, "errors": r.errors} for r in rows]})


class DataMartMetricsView(APIView):
    repository = OperationalMetricSnapshotRepository()

    def get(self, request):
        if not _has_permission(request.user, "reporting.data_mart.view"):
            return Response({"detail": "Permission required: reporting.data_mart.view"}, status=status.HTTP_403_FORBIDDEN)
        ser = ReportingMetricFilterSerializer(data=request.query_params)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        filters = ReportingFilters(
            org_id=data.get("org_id", getattr(request.user, "org_id", 0)),
            date_from=data.get("date_from"),
            date_to=data.get("date_to"),
            property_id=data.get("property_id"),
            department_id=data.get("department_id"),
            module_name=data.get("module"),
            grouping=data.get("grouping", "day"),
        )
        rows = self.repository.list_metrics(filters=filters).order_by("-snapshot_date")[:500]
        return Response({"count": rows.count(), "results": [{"id": r.id, "snapshot_date": r.snapshot_date, "snapshot_period": r.snapshot_period, "module_name": r.module_name, "metric_key": r.metric_key, "metric_value": float(r.metric_value), "metric_unit": r.metric_unit, "dimension_data": r.dimension_data} for r in rows]})


class ReportDefinitionListCreateView(APIView):
    service = ReportDefinitionService()
    repository = ReportDefinitionRepository()

    @extend_schema(request=ReportDefinitionCreateSerializer)
    def post(self, request):
        if not _has_permission(request.user, "reporting.definitions.manage"):
            return Response({"detail": "Permission required: reporting.definitions.manage"}, status=status.HTTP_403_FORBIDDEN)
        ser = ReportDefinitionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            row = self.service.create(created_by=request.user, **ser.validated_data)
        except ReportingValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=request.user.org_id, action="report_definition_created", target_type="report_definition", target_id=str(row.id), actor=request.user)
        return Response({"id": row.id, "report_code": row.report_code, "name": row.name, "is_active": row.is_active}, status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "reporting.definitions.view"):
            return Response({"detail": "Permission required: reporting.definitions.view"}, status=status.HTTP_403_FORBIDDEN)
        rows = self.repository.list()
        return Response({"count": rows.count(), "results": [{"id": r.id, "report_code": r.report_code, "name": r.name, "report_type": r.report_type, "is_active": r.is_active} for r in rows]})


class ReportDefinitionDetailView(APIView):
    service = ReportDefinitionService()
    repository = ReportDefinitionRepository()

    def get(self, request, definition_id: int):
        if not _has_permission(request.user, "reporting.definitions.view"):
            return Response({"detail": "Permission required: reporting.definitions.view"}, status=status.HTTP_403_FORBIDDEN)
        try:
            row = self.repository.get(definition_id=definition_id)
        except ReportingNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response({"id": row.id, "report_code": row.report_code, "name": row.name, "description": row.description, "module_scope": row.module_scope, "report_type": row.report_type, "default_filters": row.default_filters, "columns_config": row.columns_config, "chart_config": row.chart_config, "is_active": row.is_active})

    @extend_schema(request=ReportDefinitionUpdateSerializer)
    def patch(self, request, definition_id: int):
        if not _has_permission(request.user, "reporting.definitions.manage"):
            return Response({"detail": "Permission required: reporting.definitions.manage"}, status=status.HTTP_403_FORBIDDEN)
        ser = ReportDefinitionUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        try:
            row = self.repository.get(definition_id=definition_id)
            row = self.service.update(definition=row, updated_by=request.user, **ser.validated_data)
        except ReportingNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        _audit(request, org_id=request.user.org_id, action="report_definition_updated", target_type="report_definition", target_id=str(row.id), actor=request.user)
        return Response({"id": row.id, "name": row.name, "is_active": row.is_active})


class ReportRunView(APIView):
    service = ReportGenerationService()
    repository = ReportRunRepository()

    @extend_schema(request=ReportRunRequestSerializer)
    def post(self, request):
        if not _has_permission(request.user, "reporting.reports.run"):
            return Response({"detail": "Permission required: reporting.reports.run"}, status=status.HTTP_403_FORBIDDEN)
        ser = ReportRunRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        try:
            definition = ReportDefinitionRepository().get(definition_id=data["report_definition_id"])
            run = self.service.run_report(definition=definition, requested_by=request.user, filters=data["filters"], output_format=data["output_format"])
        except (ReportingNotFoundError, ReportingValidationError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=request.user.org_id, action="report_run_requested", target_type="report_run", target_id=str(run.id), actor=request.user)
        if run.status == "COMPLETED":
            _audit(request, org_id=request.user.org_id, action="report_run_completed", target_type="report_run", target_id=str(run.id), actor=request.user)
        if run.status == "FAILED":
            _audit(request, org_id=request.user.org_id, action="report_run_failed", target_type="report_run", target_id=str(run.id), metadata={"error": run.error_message}, actor=request.user)
        return Response({"id": run.id, "status": run.status, "storage_key": run.storage_key, "error_message": run.error_message})

    def get(self, request):
        if not _has_permission(request.user, "reporting.reports.view"):
            return Response({"detail": "Permission required: reporting.reports.view"}, status=status.HTTP_403_FORBIDDEN)
        rows = self.repository.list_recent()[:100]
        return Response({"count": len(rows), "results": [{"id": r.id, "report_definition_id": r.report_definition_id, "status": r.status, "output_format": r.output_format, "created_at": r.created_at, "completed_at": r.completed_at, "error_message": r.error_message} for r in rows]})


class ReportRunDetailView(APIView):
    repository = ReportRunRepository()

    def get(self, request, run_id: int):
        if not _has_permission(request.user, "reporting.reports.view"):
            return Response({"detail": "Permission required: reporting.reports.view"}, status=status.HTTP_403_FORBIDDEN)
        try:
            row = self.repository.get(run_id=run_id)
        except ReportingNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response({"id": row.id, "status": row.status, "filters": row.filters, "output_format": row.output_format, "storage_key": row.storage_key, "error_message": row.error_message})


class ReportRunDownloadView(APIView):
    repository = ReportRunRepository()

    def get(self, request, run_id: int):
        if not _has_permission(request.user, "reporting.reports.download"):
            return Response({"detail": "Permission required: reporting.reports.download"}, status=status.HTTP_403_FORBIDDEN)
        try:
            row = self.repository.get(run_id=run_id)
        except ReportingNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        if not row.storage_key:
            return Response({"detail": "No generated file for this run"}, status=status.HTTP_400_BAD_REQUEST)
        p = Path(row.storage_key)
        if not p.exists():
            return Response({"detail": "Generated file not found"}, status=status.HTTP_404_NOT_FOUND)
        _audit(request, org_id=request.user.org_id, action="report_downloaded", target_type="report_run", target_id=str(row.id), actor=request.user)
        return Response({"file_path": str(p), "size": p.stat().st_size})


class ReportScheduleListCreateView(APIView):
    repository = ReportScheduleRepository()
    scheduler = ReportSchedulerService()

    @extend_schema(request=ReportScheduleCreateSerializer)
    def post(self, request):
        if not _has_permission(request.user, "reporting.schedules.manage"):
            return Response({"detail": "Permission required: reporting.schedules.manage"}, status=status.HTTP_403_FORBIDDEN)
        ser = ReportScheduleCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        definition = ReportDefinitionRepository().get(definition_id=data["report_definition_id"])
        now = timezone.now()
        row = self.repository.create(
            report_definition=definition,
            name=data["name"],
            frequency_type=data["frequency_type"],
            frequency_config=data.get("frequency_config", {}),
            recipients=data.get("recipients", []),
            output_format=data["output_format"],
            filters=data.get("filters", {}),
            is_active=data.get("is_active", True),
            next_run_at=self.scheduler.calculate_next_run(frequency_type=data["frequency_type"], from_dt=now),
            created_by=request.user,
            updated_by=request.user,
        )
        _audit(request, org_id=request.user.org_id, action="report_schedule_created", target_type="report_schedule", target_id=str(row.id), actor=request.user)
        return Response({"id": row.id, "name": row.name, "next_run_at": row.next_run_at}, status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "reporting.schedules.view"):
            return Response({"detail": "Permission required: reporting.schedules.view"}, status=status.HTTP_403_FORBIDDEN)
        rows = self.repository.list()
        return Response({"count": rows.count(), "results": [{"id": r.id, "name": r.name, "frequency_type": r.frequency_type, "is_active": r.is_active, "next_run_at": r.next_run_at, "last_run_at": r.last_run_at} for r in rows]})


class ReportScheduleDetailView(APIView):
    repository = ReportScheduleRepository()

    def get(self, request, schedule_id: int):
        if not _has_permission(request.user, "reporting.schedules.view"):
            return Response({"detail": "Permission required: reporting.schedules.view"}, status=status.HTTP_403_FORBIDDEN)
        row = self.repository.get(schedule_id=schedule_id)
        return Response({"id": row.id, "name": row.name, "frequency_type": row.frequency_type, "frequency_config": row.frequency_config, "recipients": row.recipients, "output_format": row.output_format, "filters": row.filters, "is_active": row.is_active, "next_run_at": row.next_run_at, "last_run_at": row.last_run_at})

    @extend_schema(request=ReportScheduleUpdateSerializer)
    def patch(self, request, schedule_id: int):
        if not _has_permission(request.user, "reporting.schedules.manage"):
            return Response({"detail": "Permission required: reporting.schedules.manage"}, status=status.HTTP_403_FORBIDDEN)
        ser = ReportScheduleUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        row = self.repository.get(schedule_id=schedule_id)
        for k, v in ser.validated_data.items():
            setattr(row, k, v)
        row.updated_by = request.user
        row.save()
        _audit(request, org_id=request.user.org_id, action="report_schedule_updated", target_type="report_schedule", target_id=str(row.id), actor=request.user)
        return Response({"id": row.id, "is_active": row.is_active})


class ReportScheduleToggleView(APIView):
    repository = ReportScheduleRepository()
    active: bool = True

    def post(self, request, schedule_id: int):
        if not _has_permission(request.user, "reporting.schedules.manage"):
            return Response({"detail": "Permission required: reporting.schedules.manage"}, status=status.HTTP_403_FORBIDDEN)
        row = self.repository.get(schedule_id=schedule_id)
        row.is_active = self.active
        row.updated_by = request.user
        row.save(update_fields=["is_active", "updated_by", "updated_at"])
        _audit(request, org_id=request.user.org_id, action="report_schedule_activated" if self.active else "report_schedule_deactivated", target_type="report_schedule", target_id=str(row.id), actor=request.user)
        return Response({"id": row.id, "is_active": row.is_active})


class ReportScheduleRunDueView(APIView):
    scheduler = ReportSchedulerService()

    def post(self, request):
        if not _has_permission(request.user, "reporting.schedules.run"):
            return Response({"detail": "Permission required: reporting.schedules.run"}, status=status.HTTP_403_FORBIDDEN)
        summary = self.scheduler.run_due(actor_user=request.user)
        return Response(summary)


class ReportingAnalyticsBaseView(APIView):
    analytics_service = CrossModuleAnalyticsService()

    def _filters(self, request) -> ReportingFilters:
        ser = ReportingMetricFilterSerializer(data=request.query_params)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        return ReportingFilters(
            org_id=data.get("org_id", getattr(request.user, "org_id", 0)),
            date_from=data.get("date_from"),
            date_to=data.get("date_to"),
            property_id=data.get("property_id"),
            department_id=data.get("department_id"),
            module_name=data.get("module"),
            grouping=data.get("grouping", "day"),
        )


class ExecutiveSummaryAnalyticsView(ReportingAnalyticsBaseView):
    def get(self, request):
        if not _has_permission(request.user, "reporting.analytics.view"):
            return Response({"detail": "Permission required: reporting.analytics.view"}, status=status.HTTP_403_FORBIDDEN)
        payload = self.analytics_service.executive_summary(filters=self._filters(request))
        _audit(request, org_id=request.user.org_id, action="reporting_analytics_viewed", target_type="reporting_analytics", target_id="executive_summary", actor=request.user)
        return Response(payload)


class DepartmentPerformanceAnalyticsView(ReportingAnalyticsBaseView):
    def get(self, request):
        if not _has_permission(request.user, "reporting.analytics.view"):
            return Response({"detail": "Permission required: reporting.analytics.view"}, status=status.HTTP_403_FORBIDDEN)
        return Response(self.analytics_service.department_performance(filters=self._filters(request)))


class SLAAnalyticsView(ReportingAnalyticsBaseView):
    def get(self, request):
        if not _has_permission(request.user, "reporting.analytics.view"):
            return Response({"detail": "Permission required: reporting.analytics.view"}, status=status.HTTP_403_FORBIDDEN)
        return Response(self.analytics_service.sla(filters=self._filters(request)))


class CostAnalyticsView(ReportingAnalyticsBaseView):
    def get(self, request):
        if not _has_permission(request.user, "reporting.analytics.view"):
            return Response({"detail": "Permission required: reporting.analytics.view"}, status=status.HTTP_403_FORBIDDEN)
        return Response(self.analytics_service.costs(filters=self._filters(request)))


class ComplianceAnalyticsView(ReportingAnalyticsBaseView):
    def get(self, request):
        if not _has_permission(request.user, "reporting.analytics.view"):
            return Response({"detail": "Permission required: reporting.analytics.view"}, status=status.HTTP_403_FORBIDDEN)
        return Response(self.analytics_service.compliance(filters=self._filters(request)))


class EnergyAnalyticsView(ReportingAnalyticsBaseView):
    def get(self, request):
        if not _has_permission(request.user, "reporting.analytics.view"):
            return Response({"detail": "Permission required: reporting.analytics.view"}, status=status.HTTP_403_FORBIDDEN)
        return Response(self.analytics_service.energy(filters=self._filters(request)))


class ReportScheduleActivateView(ReportScheduleToggleView):
    active = True


class ReportScheduleDeactivateView(ReportScheduleToggleView):
    active = False
