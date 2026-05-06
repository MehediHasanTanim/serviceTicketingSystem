from __future__ import annotations

import io
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from infrastructure.db.core.models import (
    ComplianceCheck,
    Department,
    GuestComplaint,
    HousekeepingTask,
    InspectionRun,
    MaintenanceTask,
    OperationalMetricSnapshot,
    Project,
    ReportDataMartRun,
    ReportDefinition,
    ReportRun,
    ReportSchedule,
    RiskRegisterItem,
    ServiceOrder,
    UtilityCostRecord,
)


class ReportingValidationError(Exception):
    pass


class ReportingNotFoundError(Exception):
    pass


@dataclass
class ReportingFilters:
    org_id: int
    date_from: date | None = None
    date_to: date | None = None
    property_id: int | None = None
    department_id: int | None = None
    module_name: str | None = None
    grouping: str = "day"


class OperationalMetricSnapshotRepository:
    def upsert_snapshot(self, **kwargs) -> OperationalMetricSnapshot:
        lookup = {
            "snapshot_date": kwargs["snapshot_date"],
            "snapshot_period": kwargs["snapshot_period"],
            "module_name": kwargs["module_name"],
            "property_id": kwargs.get("property_id"),
            "department_id": kwargs.get("department_id"),
            "metric_key": kwargs["metric_key"],
        }
        defaults = {
            "metric_value": kwargs["metric_value"],
            "metric_unit": kwargs.get("metric_unit", ""),
            "dimension_data": kwargs.get("dimension_data", {}),
            "source_record_count": kwargs.get("source_record_count", 0),
            "generated_at": timezone.now(),
        }
        row, _ = OperationalMetricSnapshot.objects.update_or_create(defaults=defaults, **lookup)
        return row

    def list_metrics(self, *, filters: ReportingFilters):
        qs = OperationalMetricSnapshot.objects.filter()
        if filters.date_from:
            qs = qs.filter(snapshot_date__gte=filters.date_from)
        if filters.date_to:
            qs = qs.filter(snapshot_date__lte=filters.date_to)
        if filters.property_id:
            qs = qs.filter(property_id=filters.property_id)
        if filters.department_id:
            qs = qs.filter(department_id=filters.department_id)
        if filters.module_name:
            qs = qs.filter(module_name=filters.module_name)
        return qs


class ReportDataMartRunRepository:
    def create(self, **kwargs) -> ReportDataMartRun:
        return ReportDataMartRun.objects.create(**kwargs)

    def save(self, run: ReportDataMartRun, *, update_fields: list[str] | None = None) -> ReportDataMartRun:
        run.save(update_fields=update_fields)
        return run

    def list_recent(self):
        return ReportDataMartRun.objects.order_by("-created_at")


class ReportDefinitionRepository:
    def create(self, **kwargs) -> ReportDefinition:
        return ReportDefinition.objects.create(**kwargs)

    def list(self):
        return ReportDefinition.objects.order_by("name")

    def get(self, *, definition_id: int) -> ReportDefinition:
        row = ReportDefinition.objects.filter(id=definition_id).first()
        if not row:
            raise ReportingNotFoundError("Report definition not found")
        return row


class ReportRunRepository:
    def create(self, **kwargs) -> ReportRun:
        return ReportRun.objects.create(**kwargs)

    def get(self, *, run_id: int) -> ReportRun:
        row = ReportRun.objects.select_related("report_definition").filter(id=run_id).first()
        if not row:
            raise ReportingNotFoundError("Report run not found")
        return row

    def list_recent(self):
        return ReportRun.objects.select_related("report_definition").order_by("-created_at")


class ReportScheduleRepository:
    def create(self, **kwargs) -> ReportSchedule:
        return ReportSchedule.objects.create(**kwargs)

    def get(self, *, schedule_id: int) -> ReportSchedule:
        row = ReportSchedule.objects.select_related("report_definition").filter(id=schedule_id).first()
        if not row:
            raise ReportingNotFoundError("Report schedule not found")
        return row

    def list(self):
        return ReportSchedule.objects.select_related("report_definition").order_by("name")

    def due(self, *, now: datetime | None = None):
        current = now or timezone.now()
        return ReportSchedule.objects.select_related("report_definition").filter(is_active=True, next_run_at__lte=current)


class DataMartPipelineService:
    MODULES = {
        "service_orders": ServiceOrder,
        "housekeeping": HousekeepingTask,
        "maintenance": MaintenanceTask,
        "guest_complaints": GuestComplaint,
        "inspections": InspectionRun,
        "risk_compliance": ComplianceCheck,
        "projects": Project,
        "food_beverage": None,
        "corporate": None,
        "energy": UtilityCostRecord,
    }

    def __init__(self, *, snapshot_repository: OperationalMetricSnapshotRepository | None = None, run_repository: ReportDataMartRunRepository | None = None) -> None:
        self.snapshot_repository = snapshot_repository or OperationalMetricSnapshotRepository()
        self.run_repository = run_repository or ReportDataMartRunRepository()

    def _safe_count(self, model, *, from_date: date, to_date: date) -> int:
        if model is None:
            return 0
        if not hasattr(model, "objects"):
            return 0
        date_field = "created_at" if hasattr(model, "created_at") else None
        qs = model.objects.all()
        if date_field:
            qs = qs.filter(**{f"{date_field}__date__gte": from_date, f"{date_field}__date__lte": to_date})
        return qs.count()

    @transaction.atomic
    def refresh(self, *, period_start: date, period_end: date, run_type: str, triggered_by=None) -> ReportDataMartRun:
        run = self.run_repository.create(
            run_type=run_type,
            status=ReportDataMartRun.STATUS_RUNNING,
            period_start=period_start,
            period_end=period_end,
            started_at=timezone.now(),
            triggered_by=triggered_by,
            modules_processed=[],
            records_processed=0,
            errors=[],
        )
        modules_processed: list[str] = []
        errors: list[dict] = []
        records_processed = 0
        try:
            snapshot_day = period_end
            for module_name, model in self.MODULES.items():
                try:
                    count = self._safe_count(model, from_date=period_start, to_date=period_end)
                    self.snapshot_repository.upsert_snapshot(
                        snapshot_date=snapshot_day,
                        snapshot_period=OperationalMetricSnapshot.PERIOD_DAILY,
                        module_name=module_name,
                        property_id=None,
                        department_id=None,
                        metric_key="total_records",
                        metric_value=Decimal(str(count)),
                        metric_unit="count",
                        dimension_data={"period_start": str(period_start), "period_end": str(period_end)},
                        source_record_count=count,
                    )
                    modules_processed.append(module_name)
                    records_processed += count
                except Exception as exc:
                    errors.append({"module": module_name, "error": str(exc)})
            run.status = ReportDataMartRun.STATUS_COMPLETED if not errors else ReportDataMartRun.STATUS_FAILED
            run.modules_processed = modules_processed
            run.records_processed = records_processed
            run.errors = errors
            run.completed_at = timezone.now()
            self.run_repository.save(run, update_fields=["status", "modules_processed", "records_processed", "errors", "completed_at"])
            return run
        except Exception as exc:
            run.status = ReportDataMartRun.STATUS_FAILED
            run.errors = [{"error": str(exc)}]
            run.completed_at = timezone.now()
            self.run_repository.save(run, update_fields=["status", "errors", "completed_at"])
            return run


class ReportDefinitionService:
    def __init__(self, *, repository: ReportDefinitionRepository | None = None) -> None:
        self.repository = repository or ReportDefinitionRepository()

    def create(self, *, created_by, **payload) -> ReportDefinition:
        code = payload["report_code"].strip().upper()
        if not code.replace("_", "").isalnum():
            raise ReportingValidationError("report_code must be human-readable alphanumeric/underscore")
        return self.repository.create(
            report_code=code,
            name=payload["name"],
            description=payload.get("description", ""),
            module_scope=payload.get("module_scope", []),
            report_type=payload["report_type"],
            default_filters=payload.get("default_filters", {}),
            columns_config=payload.get("columns_config", []),
            chart_config=payload.get("chart_config", {}),
            is_active=payload.get("is_active", True),
            created_by=created_by,
            updated_by=created_by,
        )

    def update(self, *, definition: ReportDefinition, updated_by, **payload) -> ReportDefinition:
        for field in ["name", "description", "module_scope", "report_type", "default_filters", "columns_config", "chart_config", "is_active"]:
            if field in payload:
                setattr(definition, field, payload[field])
        definition.updated_by = updated_by
        definition.save()
        return definition


class ReportBuilderService:
    def _safe_avg_hours(self, qs, start_field: str, end_field: str) -> Decimal:
        total_hours = Decimal("0")
        total = 0
        for row in qs:
            start = getattr(row, start_field, None)
            end = getattr(row, end_field, None)
            if start and end and end >= start:
                total_hours += Decimal(str((end - start).total_seconds() / 3600))
                total += 1
        if total == 0:
            return Decimal("0")
        return (total_hours / Decimal(total)).quantize(Decimal("0.01"))

    def build_operational_summary(self, *, filters: ReportingFilters) -> dict:
        modules = {
            "service_orders": ServiceOrder.objects.filter(org_id=filters.org_id),
            "housekeeping": HousekeepingTask.objects.filter(room__property__org_id=filters.org_id),
            "maintenance": MaintenanceTask.objects.filter(org_id=filters.org_id),
            "guest_complaints": GuestComplaint.objects.filter(org_id=filters.org_id),
            "inspections": InspectionRun.objects.filter(org_id=filters.org_id),
            "risk_compliance": ComplianceCheck.objects.filter(requirement__org_id=filters.org_id),
            "projects": Project.objects.filter(org_id=filters.org_id),
        }
        open_by_module = {}
        completed_by_module = {}
        for name, qs in modules.items():
            if filters.date_from:
                qs = qs.filter(created_at__date__gte=filters.date_from)
            if filters.date_to:
                qs = qs.filter(created_at__date__lte=filters.date_to)
            if hasattr(qs.model, "property_id") and filters.property_id:
                qs = qs.filter(property_id=filters.property_id)
            if hasattr(qs.model, "department_id") and filters.department_id:
                qs = qs.filter(department_id=filters.department_id)
            if hasattr(qs.model, "status"):
                open_by_module[name] = qs.filter(~Q(status__in=["COMPLETED", "CANCELLED", "VOID", "RESOLVED", "CLOSED", "PAID"])).count()
                completed_by_module[name] = qs.filter(status__in=["COMPLETED", "RESOLVED", "CLOSED", "PAID"]).count()
            else:
                open_by_module[name] = 0
                completed_by_module[name] = 0

        resolution_hours = self._safe_avg_hours(
            GuestComplaint.objects.filter(org_id=filters.org_id, resolved_at__isnull=False),
            "created_at",
            "resolved_at",
        )
        return {
            "open_tasks_by_module": open_by_module,
            "completed_tasks_by_module": completed_by_module,
            "overdue_items_by_module": {
                "service_orders": ServiceOrder.objects.filter(org_id=filters.org_id, due_date__lt=timezone.now().date()).exclude(status=ServiceOrder.STATUS_COMPLETED).count(),
                "maintenance": MaintenanceTask.objects.filter(org_id=filters.org_id, due_at__lt=timezone.now()).exclude(status=MaintenanceTask.STATUS_COMPLETED).count(),
            },
            "average_resolution_hours": float(resolution_hours),
            "total_operational_cost": float(
                (ServiceOrder.objects.filter(org_id=filters.org_id).aggregate(total=Sum("total_cost"))["total"] or Decimal("0"))
                + (MaintenanceTask.objects.filter(org_id=filters.org_id).aggregate(total=Sum("total_cost"))["total"] or Decimal("0"))
                + (UtilityCostRecord.objects.filter(org_id=filters.org_id).aggregate(total=Sum("total_cost"))["total"] or Decimal("0"))
            ),
            "compliance_rate": float(
                Decimal(ComplianceCheck.objects.filter(requirement__org_id=filters.org_id, status=ComplianceCheck.STATUS_COMPLIANT).count())
                / Decimal(max(1, ComplianceCheck.objects.filter(requirement__org_id=filters.org_id).count()))
                * Decimal("100")
            ),
            "guest_satisfaction_score": float(GuestComplaint.objects.filter(org_id=filters.org_id).aggregate(avg=Avg("satisfaction_score"))["avg"] or 0),
            "energy_efficiency_kpi": float(UtilityCostRecord.objects.filter(org_id=filters.org_id).aggregate(avg=Avg("normalized_usage_value"))["avg"] or 0),
        }


class ExcelExportService:
    def export(self, *, title: str, filters: dict, rows: list[dict]) -> tuple[str, bytes]:
        try:
            from openpyxl import Workbook
        except Exception as exc:
            raise ReportingValidationError("Excel export dependency missing: openpyxl") from exc
        wb = Workbook()
        ws = wb.active
        ws.title = "Report"
        ws.append([title])
        ws.append(["Generated at", timezone.now().isoformat()])
        ws.append(["Filters", json.dumps(filters)])
        ws.append([])
        headers = list(rows[0].keys()) if rows else ["message"]
        ws.append(headers)
        if rows:
            for row in rows:
                ws.append([row.get(k) for k in headers])
        else:
            ws.append(["No data"])
        buffer = io.BytesIO()
        wb.save(buffer)
        return "report.xlsx", buffer.getvalue()


class PDFExportService:
    def export(self, *, title: str, filters: dict, summary: dict, rows: list[dict]) -> tuple[str, bytes]:
        # Minimal standards-compliant PDF for portability without external deps.
        lines = [title, f"Generated at: {timezone.now().isoformat()}", f"Filters: {json.dumps(filters)}", f"Summary: {json.dumps(summary)}", "Rows:"]
        lines.extend([json.dumps(r) for r in rows[:100]])
        text = "\\n".join(lines).replace("(", "[").replace(")", "]")
        stream = f"BT /F1 10 Tf 40 780 Td ({text[:3000]}) Tj ET"
        pdf = f"%PDF-1.4\n1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>endobj\n4 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n5 0 obj<< /Length {len(stream)} >>stream\n{stream}\nendstream endobj\nxref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000243 00000 n \n0000000313 00000 n \ntrailer<< /Size 6 /Root 1 0 R >>\nstartxref\n0\n%%EOF".encode("utf-8")
        return "report.pdf", pdf


class ReportEmailDeliveryService:
    def send(self, *, subject: str, body: str, recipients: list[str], attachment_name: str, attachment_bytes: bytes, mime_type: str) -> int:
        if not recipients:
            return 0
        email = EmailMessage(subject=subject, body=body, from_email=settings.DEFAULT_FROM_EMAIL, to=recipients)
        email.attach(attachment_name, attachment_bytes, mime_type)
        return email.send(fail_silently=False)


class ReportGenerationService:
    def __init__(self, *, run_repository: ReportRunRepository | None = None, definition_repository: ReportDefinitionRepository | None = None) -> None:
        self.run_repository = run_repository or ReportRunRepository()
        self.definition_repository = definition_repository or ReportDefinitionRepository()
        self.builder = ReportBuilderService()
        self.excel = ExcelExportService()
        self.pdf = PDFExportService()

    def _storage_path(self, *, run_id: int, filename: str) -> Path:
        root = Path(settings.BASE_DIR) / "tmp" / "report_exports"
        root.mkdir(parents=True, exist_ok=True)
        return root / f"{run_id}_{filename}"

    @transaction.atomic
    def run_report(self, *, definition: ReportDefinition, requested_by, filters: dict, output_format: str) -> ReportRun:
        if not definition.is_active:
            raise ReportingValidationError("Inactive report definition cannot run")
        report_run = self.run_repository.create(
            report_definition=definition,
            report_name=definition.name,
            status=ReportRun.STATUS_RUNNING,
            requested_by=requested_by,
            filters=filters,
            output_format=output_format,
            started_at=timezone.now(),
        )
        try:
            assembled_filters = ReportingFilters(
                org_id=filters["org_id"],
                date_from=filters.get("date_from"),
                date_to=filters.get("date_to"),
                property_id=filters.get("property_id"),
                department_id=filters.get("department_id"),
                module_name=filters.get("module"),
                grouping=filters.get("grouping", "day"),
            )
            payload = self.builder.build_operational_summary(filters=assembled_filters)
            rows = [{"module": k, "open": payload["open_tasks_by_module"].get(k, 0), "completed": payload["completed_tasks_by_module"].get(k, 0)} for k in payload["open_tasks_by_module"].keys()]
            if output_format == ReportRun.FORMAT_JSON:
                report_run.storage_key = ""
            elif output_format == ReportRun.FORMAT_EXCEL:
                name, blob = self.excel.export(title=definition.name, filters=filters, rows=rows)
                path = self._storage_path(run_id=report_run.id, filename=name)
                path.write_bytes(blob)
                report_run.storage_key = str(path)
            elif output_format == ReportRun.FORMAT_PDF:
                name, blob = self.pdf.export(title=definition.name, filters=filters, summary=payload, rows=rows)
                path = self._storage_path(run_id=report_run.id, filename=name)
                path.write_bytes(blob)
                report_run.storage_key = str(path)
            else:
                raise ReportingValidationError("Unsupported format")
            report_run.status = ReportRun.STATUS_COMPLETED
            report_run.completed_at = timezone.now()
            report_run.save(update_fields=["status", "storage_key", "completed_at"])
            return report_run
        except Exception as exc:
            report_run.status = ReportRun.STATUS_FAILED
            report_run.error_message = str(exc)
            report_run.completed_at = timezone.now()
            report_run.save(update_fields=["status", "error_message", "completed_at"])
            return report_run


class ReportSchedulerService:
    def __init__(self, *, schedule_repository: ReportScheduleRepository | None = None, generation_service: ReportGenerationService | None = None, email_delivery: ReportEmailDeliveryService | None = None) -> None:
        self.schedule_repository = schedule_repository or ReportScheduleRepository()
        self.generation_service = generation_service or ReportGenerationService()
        self.email_delivery = email_delivery or ReportEmailDeliveryService()

    def calculate_next_run(self, *, frequency_type: str, from_dt: datetime) -> datetime:
        if frequency_type == ReportSchedule.FREQ_DAILY:
            return from_dt + timedelta(days=1)
        if frequency_type == ReportSchedule.FREQ_WEEKLY:
            return from_dt + timedelta(weeks=1)
        if frequency_type == ReportSchedule.FREQ_MONTHLY:
            return from_dt + timedelta(days=30)
        return from_dt + timedelta(days=90)

    @transaction.atomic
    def run_due(self, *, actor_user=None) -> dict:
        now = timezone.now()
        due = self.schedule_repository.due(now=now)
        summary = {"schedules_checked": due.count(), "reports_generated": 0, "emails_sent": 0, "failures": 0}
        for schedule in due:
            try:
                run = self.generation_service.run_report(
                    definition=schedule.report_definition,
                    requested_by=actor_user or schedule.created_by,
                    filters=schedule.filters,
                    output_format=schedule.output_format,
                )
                if run.status == ReportRun.STATUS_COMPLETED:
                    summary["reports_generated"] += 1
                    if run.storage_key and schedule.recipients:
                        blob = Path(run.storage_key).read_bytes()
                        sent = self.email_delivery.send(
                            subject=f"Scheduled Report: {schedule.name}",
                            body="Attached scheduled report.",
                            recipients=schedule.recipients,
                            attachment_name=Path(run.storage_key).name,
                            attachment_bytes=blob,
                            mime_type="application/octet-stream",
                        )
                        summary["emails_sent"] += sent
                else:
                    summary["failures"] += 1
                schedule.last_run_at = now
                schedule.next_run_at = self.calculate_next_run(frequency_type=schedule.frequency_type, from_dt=now)
                schedule.save(update_fields=["last_run_at", "next_run_at", "updated_at"])
            except Exception:
                summary["failures"] += 1
        return summary


class CrossModuleAnalyticsService:
    def __init__(self, *, builder: ReportBuilderService | None = None, snapshot_repository: OperationalMetricSnapshotRepository | None = None) -> None:
        self.builder = builder or ReportBuilderService()
        self.snapshot_repository = snapshot_repository or OperationalMetricSnapshotRepository()

    def executive_summary(self, *, filters: ReportingFilters) -> dict:
        return self.builder.build_operational_summary(filters=filters)

    def department_performance(self, *, filters: ReportingFilters) -> dict:
        base = self.builder.build_operational_summary(filters=filters)
        return {"department_id": filters.department_id, **base}

    def sla(self, *, filters: ReportingFilters) -> dict:
        base = self.builder.build_operational_summary(filters=filters)
        open_tasks = sum(base["open_tasks_by_module"].values())
        completed = sum(base["completed_tasks_by_module"].values())
        total = max(1, open_tasks + completed)
        return {"sla_compliance_percent": float(Decimal(completed) / Decimal(total) * Decimal("100")), **base}

    def costs(self, *, filters: ReportingFilters) -> dict:
        base = self.builder.build_operational_summary(filters=filters)
        return {"total_operational_cost": base["total_operational_cost"]}

    def compliance(self, *, filters: ReportingFilters) -> dict:
        base = self.builder.build_operational_summary(filters=filters)
        return {"compliance_rate": base["compliance_rate"]}

    def energy(self, *, filters: ReportingFilters) -> dict:
        base = self.builder.build_operational_summary(filters=filters)
        return {"energy_efficiency_kpi": base["energy_efficiency_kpi"]}
