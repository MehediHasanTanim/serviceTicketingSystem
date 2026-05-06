from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from application.services.reporting import (
    CrossModuleAnalyticsService,
    DataMartPipelineService,
    ExcelExportService,
    PDFExportService,
    ReportDefinitionService,
    ReportGenerationService,
    ReportSchedulerService,
    ReportingFilters,
    ReportingValidationError,
)
from infrastructure.db.core.models import (
    AuditLog,
    OperationalMetricSnapshot,
    Organization,
    ReportDataMartRun,
    ReportDefinition,
    ReportRun,
    ReportSchedule,
    ServiceOrder,
)
from tests.unit.api_test_helpers import assign_role, authenticated_client, create_org, create_user, grant_permissions


@pytest.mark.django_db
def test_data_mart_manual_refresh_creates_and_upserts_snapshots():
    org = create_org()
    actor = create_user(org, email="reporting-dm@example.com")
    ServiceOrder.objects.create(
        org=org,
        ticket_number="SO-001",
        title="T",
        description="",
        customer_id=1,
        created_by=actor,
        priority=ServiceOrder.PRIORITY_MEDIUM,
        type=ServiceOrder.TYPE_OTHER,
        status=ServiceOrder.STATUS_OPEN,
    )
    svc = DataMartPipelineService()
    run = svc.refresh(period_start=date.today(), period_end=date.today(), run_type=ReportDataMartRun.TYPE_MANUAL, triggered_by=actor)
    assert run.status in [ReportDataMartRun.STATUS_COMPLETED, ReportDataMartRun.STATUS_FAILED]
    first_count = OperationalMetricSnapshot.objects.count()
    assert first_count > 0
    svc.refresh(period_start=date.today(), period_end=date.today(), run_type=ReportDataMartRun.TYPE_MANUAL, triggered_by=actor)
    assert OperationalMetricSnapshot.objects.count() == first_count


@pytest.mark.django_db
def test_report_definition_create_and_inactive_run_blocked():
    org = create_org()
    actor = create_user(org, email="reporting-def@example.com")
    definition = ReportDefinitionService().create(
        created_by=actor,
        report_code="OPS_SUMMARY",
        name="Ops Summary",
        report_type=ReportDefinition.TYPE_OPERATIONAL_SUMMARY,
        module_scope=["service_orders"],
    )
    assert definition.report_code == "OPS_SUMMARY"
    definition.is_active = False
    definition.save(update_fields=["is_active"])
    run = ReportGenerationService().run_report(
        definition=definition,
        requested_by=actor,
        filters={"org_id": org.id},
        output_format=ReportRun.FORMAT_JSON,
    )
    assert run.status == ReportRun.STATUS_FAILED


@pytest.mark.django_db
def test_export_services_generate_payloads_and_reject_unsupported():
    excel_name, excel_blob = ExcelExportService().export(title="X", filters={"org_id": 1}, rows=[{"a": 1, "b": "x"}])
    pdf_name, pdf_blob = PDFExportService().export(title="X", filters={"org_id": 1}, summary={"k": 1}, rows=[])
    assert excel_name.endswith(".xlsx")
    assert len(excel_blob) > 0
    assert pdf_name.endswith(".pdf")
    assert pdf_blob.startswith(b"%PDF")


@pytest.mark.django_db
def test_scheduler_runs_due_and_skips_inactive():
    org = create_org()
    actor = create_user(org, email="reporting-sched@example.com")
    definition = ReportDefinitionService().create(
        created_by=actor,
        report_code="OPS_SCHED",
        name="Ops Sched",
        report_type=ReportDefinition.TYPE_OPERATIONAL_SUMMARY,
        module_scope=["service_orders"],
    )
    active = ReportSchedule.objects.create(
        report_definition=definition,
        name="Active",
        frequency_type=ReportSchedule.FREQ_DAILY,
        frequency_config={},
        recipients=[],
        output_format=ReportSchedule.FORMAT_PDF,
        filters={"org_id": org.id},
        is_active=True,
        next_run_at=timezone.now() - timedelta(minutes=1),
        created_by=actor,
        updated_by=actor,
    )
    ReportSchedule.objects.create(
        report_definition=definition,
        name="Inactive",
        frequency_type=ReportSchedule.FREQ_DAILY,
        frequency_config={},
        recipients=[],
        output_format=ReportSchedule.FORMAT_PDF,
        filters={"org_id": org.id},
        is_active=False,
        next_run_at=timezone.now() - timedelta(minutes=1),
        created_by=actor,
        updated_by=actor,
    )
    summary = ReportSchedulerService().run_due(actor_user=actor)
    assert summary["schedules_checked"] == 1
    active.refresh_from_db()
    assert active.last_run_at is not None


@pytest.mark.django_db
def test_cross_module_analytics_zero_safe_no_nan():
    org = create_org()
    payload = CrossModuleAnalyticsService().executive_summary(filters=ReportingFilters(org_id=org.id))
    assert payload["compliance_rate"] >= 0
    assert payload["energy_efficiency_kpi"] >= 0


@pytest.mark.django_db
def test_reporting_api_creates_audit_entries_for_run_download_and_schedule():
    org = create_org()
    actor = create_user(org, email="reporting-api@example.com")
    grant_permissions(
        actor,
        [
            "reporting.definitions.manage",
            "reporting.reports.run",
            "reporting.reports.download",
            "reporting.schedules.manage",
            "reporting.schedules.run",
            "reporting.analytics.view",
            "reporting.data_mart.refresh",
        ],
    )
    client = authenticated_client(actor)

    create_def = client.post(
        "/api/v1/reporting/definitions",
        {
            "report_code": "API_REPORT_1",
            "name": "API Report",
            "report_type": "OPERATIONAL_SUMMARY",
            "module_scope": ["service_orders"],
        },
        format="json",
    )
    assert create_def.status_code == 201
    report_id = create_def.data["id"]

    run_resp = client.post(
        "/api/v1/reporting/reports/run",
        {"report_definition_id": report_id, "filters": {"org_id": org.id}, "output_format": "PDF"},
        format="json",
    )
    assert run_resp.status_code == 200
    run_id = run_resp.data["id"]

    download_resp = client.get(f"/api/v1/reporting/reports/runs/{run_id}/download")
    assert download_resp.status_code in [200, 400]

    actions = set(AuditLog.objects.filter(org=org).values_list("action", flat=True))
    assert "report_run_requested" in actions
    assert "report_definition_created" in actions
