from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Q, QuerySet, Sum
from django.utils import timezone

from infrastructure.db.core.models import (
    Asset,
    AssetLifecycleHistory,
    MaintenanceLogbookEntry,
    MaintenanceLaborEntry,
    MaintenancePartEntry,
    MaintenanceTask,
    PMSchedule,
    User,
)


class MaintenanceError(Exception):
    pass


class MaintenanceValidationError(MaintenanceError):
    pass


class MaintenanceNotFoundError(MaintenanceError):
    pass


class MaintenanceTransitionError(MaintenanceError):
    pass


class AssetLifecycleValidator:
    ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        Asset.STATUS_ACTIVE: {Asset.STATUS_UNDER_MAINTENANCE, Asset.STATUS_OUT_OF_SERVICE, Asset.STATUS_RETIRED},
        Asset.STATUS_UNDER_MAINTENANCE: {Asset.STATUS_ACTIVE, Asset.STATUS_OUT_OF_SERVICE, Asset.STATUS_RETIRED},
        Asset.STATUS_OUT_OF_SERVICE: {Asset.STATUS_UNDER_MAINTENANCE, Asset.STATUS_RETIRED},
        Asset.STATUS_INACTIVE: {Asset.STATUS_ACTIVE, Asset.STATUS_RETIRED},
        Asset.STATUS_RETIRED: set(),
    }

    def validate(self, from_status: str, to_status: str) -> None:
        allowed = self.ALLOWED_TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            raise MaintenanceTransitionError(f"Invalid asset transition from {from_status} to {to_status}")


class MaintenanceTaskLifecycleValidator:
    ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        MaintenanceTask.STATUS_OPEN: {
            MaintenanceTask.STATUS_ASSIGNED,
            MaintenanceTask.STATUS_IN_PROGRESS,
            MaintenanceTask.STATUS_ON_HOLD,
            MaintenanceTask.STATUS_CANCELLED,
            MaintenanceTask.STATUS_VOID,
        },
        MaintenanceTask.STATUS_ASSIGNED: {
            MaintenanceTask.STATUS_IN_PROGRESS,
            MaintenanceTask.STATUS_ON_HOLD,
            MaintenanceTask.STATUS_CANCELLED,
            MaintenanceTask.STATUS_VOID,
        },
        MaintenanceTask.STATUS_IN_PROGRESS: {
            MaintenanceTask.STATUS_ON_HOLD,
            MaintenanceTask.STATUS_COMPLETED,
            MaintenanceTask.STATUS_CANCELLED,
            MaintenanceTask.STATUS_VOID,
        },
        MaintenanceTask.STATUS_ON_HOLD: {
            MaintenanceTask.STATUS_ASSIGNED,
            MaintenanceTask.STATUS_IN_PROGRESS,
            MaintenanceTask.STATUS_CANCELLED,
            MaintenanceTask.STATUS_VOID,
        },
        MaintenanceTask.STATUS_COMPLETED: set(),
        MaintenanceTask.STATUS_CANCELLED: set(),
        MaintenanceTask.STATUS_VOID: set(),
    }

    def validate(self, from_status: str, to_status: str) -> None:
        allowed = self.ALLOWED_TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            raise MaintenanceTransitionError(f"Invalid maintenance task transition from {from_status} to {to_status}")


class MaintenanceCostCalculator:
    ZERO = Decimal("0.00")

    def norm(self, value: Decimal | str | int | float | None, field_name: str = "value") -> Decimal:
        val = Decimal(str(value if value is not None else self.ZERO)).quantize(Decimal("0.01"))
        if val < self.ZERO:
            raise MaintenanceValidationError(f"{field_name} cannot be negative")
        return val

    def compute_task_totals(self, task: MaintenanceTask) -> dict[str, Decimal]:
        part_total = (
            MaintenancePartEntry.objects.filter(logbook_entry__maintenance_task=task).aggregate(total=Sum("total_cost"))["total"]
            or self.ZERO
        )
        labor_total = (
            MaintenanceLaborEntry.objects.filter(logbook_entry__maintenance_task=task).aggregate(total=Sum("total_labor_cost"))["total"]
            or self.ZERO
        )
        part_total = self.norm(part_total, "parts_total")
        labor_total = self.norm(labor_total, "labor_total")
        return {
            "parts_total": part_total,
            "labor_total": labor_total,
            "grand_total": (part_total + labor_total).quantize(Decimal("0.01")),
        }


@dataclass
class AssetFilters:
    org_id: int
    status: str | None = None
    category: str | None = None
    location_id: int | None = None
    room_id: int | None = None
    department_id: int | None = None
    property_id: int | None = None
    criticality: str | None = None
    warranty_expiring_before: date | None = None


@dataclass
class MaintenanceTaskFilters:
    org_id: int
    task_type: str | None = None
    status: str | None = None
    priority: str | None = None
    asset_id: int | None = None
    room_id: int | None = None
    property_id: int | None = None
    department_id: int | None = None
    assigned_to: int | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class AssetRepository:
    def create(self, **kwargs) -> Asset:
        return Asset.objects.create(**kwargs)

    def get_for_org(self, *, asset_id: int, org_id: int) -> Asset:
        try:
            return Asset.objects.get(id=asset_id, org_id=org_id)
        except Asset.DoesNotExist as exc:
            raise MaintenanceNotFoundError("Asset not found") from exc

    def get_by_qr_for_org(self, *, org_id: int, qr_code: str) -> Asset:
        try:
            return Asset.objects.get(org_id=org_id, qr_code=qr_code)
        except Asset.DoesNotExist as exc:
            raise MaintenanceNotFoundError("Asset not found") from exc

    def list(self, filters: AssetFilters) -> QuerySet[Asset]:
        qs = Asset.objects.filter(org_id=filters.org_id)
        if filters.status:
            qs = qs.filter(status=filters.status)
        if filters.category:
            qs = qs.filter(category__iexact=filters.category)
        if filters.location_id:
            qs = qs.filter(location_id=filters.location_id)
        if filters.room_id:
            qs = qs.filter(room_id=filters.room_id)
        if filters.department_id:
            qs = qs.filter(department_id=filters.department_id)
        if filters.property_id:
            qs = qs.filter(property_id=filters.property_id)
        if filters.criticality:
            qs = qs.filter(criticality=filters.criticality)
        if filters.warranty_expiring_before:
            qs = qs.filter(warranty_expiry_date__lte=filters.warranty_expiring_before)
        return qs

    def save(self, asset: Asset, *, update_fields: list[str] | None = None) -> Asset:
        asset.save(update_fields=update_fields)
        return asset


class AssetLifecycleHistoryRepository:
    def create(self, **kwargs) -> AssetLifecycleHistory:
        return AssetLifecycleHistory.objects.create(**kwargs)

    def list_for_asset(self, *, asset_id: int) -> QuerySet[AssetLifecycleHistory]:
        return AssetLifecycleHistory.objects.filter(asset_id=asset_id).order_by("-changed_at")


class MaintenanceTaskRepository:
    def create(self, **kwargs) -> MaintenanceTask:
        return MaintenanceTask.objects.create(**kwargs)

    def get_for_org(self, *, task_id: int, org_id: int) -> MaintenanceTask:
        try:
            return MaintenanceTask.objects.get(id=task_id, org_id=org_id)
        except MaintenanceTask.DoesNotExist as exc:
            raise MaintenanceNotFoundError("Maintenance task not found") from exc

    def list(self, filters: MaintenanceTaskFilters) -> QuerySet[MaintenanceTask]:
        qs = MaintenanceTask.objects.filter(org_id=filters.org_id)
        if filters.task_type:
            qs = qs.filter(task_type=filters.task_type)
        if filters.status:
            qs = qs.filter(status=filters.status)
        if filters.priority:
            qs = qs.filter(priority=filters.priority)
        if filters.asset_id:
            qs = qs.filter(asset_id=filters.asset_id)
        if filters.room_id:
            qs = qs.filter(room_id=filters.room_id)
        if filters.property_id:
            qs = qs.filter(property_id=filters.property_id)
        if filters.department_id:
            qs = qs.filter(department_id=filters.department_id)
        if filters.assigned_to:
            qs = qs.filter(assigned_to_id=filters.assigned_to)
        if filters.date_from:
            qs = qs.filter(created_at__gte=filters.date_from)
        if filters.date_to:
            qs = qs.filter(created_at__lte=filters.date_to)
        return qs

    def exists_active_for_pm_schedule(self, *, schedule_id: int) -> bool:
        return MaintenanceTask.objects.filter(
            pm_schedule_id=schedule_id,
            task_type=MaintenanceTask.TYPE_PREVENTIVE,
            status__in=[
                MaintenanceTask.STATUS_OPEN,
                MaintenanceTask.STATUS_ASSIGNED,
                MaintenanceTask.STATUS_IN_PROGRESS,
                MaintenanceTask.STATUS_ON_HOLD,
            ],
        ).exists()

    def save(self, task: MaintenanceTask, *, update_fields: list[str] | None = None) -> MaintenanceTask:
        task.save(update_fields=update_fields)
        return task


class PMScheduleRepository:
    def create(self, **kwargs) -> PMSchedule:
        return PMSchedule.objects.create(**kwargs)

    def get_due_schedules(self, *, now: datetime | None = None) -> QuerySet[PMSchedule]:
        current = now or timezone.now()
        return PMSchedule.objects.filter(is_active=True, next_run_at__lte=current).select_related("asset")

    def save(self, schedule: PMSchedule, *, update_fields: list[str] | None = None) -> PMSchedule:
        schedule.save(update_fields=update_fields)
        return schedule


class MaintenanceLogbookRepository:
    def create_entry(self, **kwargs) -> MaintenanceLogbookEntry:
        return MaintenanceLogbookEntry.objects.create(**kwargs)

    def list_for_task(self, *, task_id: int) -> QuerySet[MaintenanceLogbookEntry]:
        return (
            MaintenanceLogbookEntry.objects.filter(maintenance_task_id=task_id)
            .prefetch_related("parts_entries", "labor_entries")
            .order_by("created_at")
        )


class AssetService:
    def __init__(
        self,
        *,
        asset_repository: AssetRepository | None = None,
        history_repository: AssetLifecycleHistoryRepository | None = None,
        lifecycle_validator: AssetLifecycleValidator | None = None,
    ) -> None:
        self.asset_repository = asset_repository or AssetRepository()
        self.history_repository = history_repository or AssetLifecycleHistoryRepository()
        self.lifecycle_validator = lifecycle_validator or AssetLifecycleValidator()

    def _asset_code(self, asset_id: int) -> str:
        return f"AST-{asset_id:08d}"

    @transaction.atomic
    def create_asset(self, *, created_by: User, org_id: int, **payload) -> Asset:
        asset = self.asset_repository.create(
            org_id=org_id,
            asset_code=payload.get("asset_code") or f"TMP-{timezone.now().timestamp()}",
            qr_code=payload.get("qr_code"),
            name=payload["name"],
            description=payload.get("description", ""),
            category=payload.get("category", ""),
            location_id=payload.get("location_id"),
            room_id=payload.get("room_id"),
            department_id=payload.get("department_id"),
            property_id=payload.get("property_id"),
            manufacturer=payload.get("manufacturer", ""),
            model_number=payload.get("model_number", ""),
            serial_number=payload.get("serial_number", ""),
            purchase_date=payload.get("purchase_date"),
            warranty_expiry_date=payload.get("warranty_expiry_date"),
            status=payload.get("status", Asset.STATUS_ACTIVE),
            criticality=payload.get("criticality", Asset.CRITICALITY_MEDIUM),
            created_by=created_by,
            updated_by=created_by,
        )
        if asset.asset_code.startswith("TMP-"):
            asset.asset_code = self._asset_code(asset.id)
            self.asset_repository.save(asset, update_fields=["asset_code", "updated_at"])
        self.history_repository.create(
            asset=asset,
            previous_status=asset.status,
            new_status=asset.status,
            changed_by=created_by,
            reason="Initial status",
            metadata_json={},
        )
        return asset

    def list_assets(self, *, filters: AssetFilters) -> QuerySet[Asset]:
        return self.asset_repository.list(filters)

    def get_asset(self, *, asset_id: int, org_id: int) -> Asset:
        return self.asset_repository.get_for_org(asset_id=asset_id, org_id=org_id)

    @transaction.atomic
    def update_asset(self, *, asset: Asset, updated_by: User, **payload) -> Asset:
        for key in [
            "name",
            "description",
            "category",
            "location_id",
            "room_id",
            "department_id",
            "property_id",
            "manufacturer",
            "model_number",
            "serial_number",
            "purchase_date",
            "warranty_expiry_date",
            "criticality",
            "qr_code",
        ]:
            if key in payload:
                setattr(asset, key, payload[key])
        asset.updated_by = updated_by
        self.asset_repository.save(asset)
        return asset

    @transaction.atomic
    def change_status(
        self,
        *,
        asset: Asset,
        new_status: str,
        changed_by: User,
        reason: str = "",
        metadata: dict | None = None,
    ) -> Asset:
        old_status = asset.status
        self.lifecycle_validator.validate(old_status, new_status)
        asset.status = new_status
        asset.updated_by = changed_by
        self.asset_repository.save(asset)
        self.history_repository.create(
            asset=asset,
            previous_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
            metadata_json=metadata or {},
        )
        return asset


class MaintenanceService:
    def __init__(
        self,
        *,
        task_repository: MaintenanceTaskRepository | None = None,
        lifecycle_validator: MaintenanceTaskLifecycleValidator | None = None,
    ) -> None:
        self.task_repository = task_repository or MaintenanceTaskRepository()
        self.lifecycle_validator = lifecycle_validator or MaintenanceTaskLifecycleValidator()

    def _task_number(self, task_id: int) -> str:
        return f"MT-{task_id:08d}"

    @transaction.atomic
    def create_task(self, *, reported_by: User, org_id: int, **payload) -> MaintenanceTask:
        task_type = payload.get("task_type", MaintenanceTask.TYPE_CORRECTIVE)
        task = self.task_repository.create(
            org_id=org_id,
            task_number=f"TMP-{timezone.now().timestamp()}",
            task_type=task_type,
            title=payload["title"],
            description=payload.get("description", ""),
            asset_id=payload.get("asset_id"),
            room_id=payload.get("room_id"),
            property_id=payload.get("property_id"),
            department_id=payload.get("department_id"),
            priority=payload.get("priority", MaintenanceTask.PRIORITY_MEDIUM),
            status=MaintenanceTask.STATUS_OPEN,
            assigned_to=payload.get("assigned_to"),
            reported_by=reported_by,
            scheduled_at=payload.get("scheduled_at"),
            due_at=payload.get("due_at"),
            pm_schedule_id=payload.get("pm_schedule_id"),
        )
        task.task_number = self._task_number(task.id)
        self.task_repository.save(task, update_fields=["task_number", "updated_at"])
        if task.assigned_to_id:
            self.transition(task=task, to_status=MaintenanceTask.STATUS_ASSIGNED)
        return task

    def list_tasks(self, *, filters: MaintenanceTaskFilters) -> QuerySet[MaintenanceTask]:
        return self.task_repository.list(filters)

    def get_task(self, *, task_id: int, org_id: int) -> MaintenanceTask:
        return self.task_repository.get_for_org(task_id=task_id, org_id=org_id)

    @transaction.atomic
    def update_task(self, *, task: MaintenanceTask, **payload) -> MaintenanceTask:
        if task.status in {MaintenanceTask.STATUS_COMPLETED, MaintenanceTask.STATUS_CANCELLED, MaintenanceTask.STATUS_VOID}:
            raise MaintenanceValidationError("Completed/cancelled/void task cannot be modified")
        for key in ["title", "description", "priority", "asset_id", "room_id", "property_id", "department_id", "scheduled_at", "due_at"]:
            if key in payload:
                setattr(task, key, payload[key])
        self.task_repository.save(task)
        return task

    @transaction.atomic
    def assign(self, *, task: MaintenanceTask, assignee: User) -> MaintenanceTask:
        task.assigned_to = assignee
        self.transition(task=task, to_status=MaintenanceTask.STATUS_ASSIGNED)
        return task

    @transaction.atomic
    def transition(self, *, task: MaintenanceTask, to_status: str) -> MaintenanceTask:
        self.lifecycle_validator.validate(task.status, to_status)
        task.status = to_status
        if to_status == MaintenanceTask.STATUS_IN_PROGRESS:
            task.started_at = timezone.now()
        if to_status == MaintenanceTask.STATUS_COMPLETED:
            task.completed_at = timezone.now()
        self.task_repository.save(task)
        return task


class PMSchedulerService:
    def __init__(
        self,
        *,
        schedule_repository: PMScheduleRepository | None = None,
        task_repository: MaintenanceTaskRepository | None = None,
        maintenance_service: MaintenanceService | None = None,
    ) -> None:
        self.schedule_repository = schedule_repository or PMScheduleRepository()
        self.task_repository = task_repository or MaintenanceTaskRepository()
        self.maintenance_service = maintenance_service or MaintenanceService(task_repository=self.task_repository)

    def _compute_next_run(self, schedule: PMSchedule, base: datetime | None = None) -> datetime:
        at = base or schedule.next_run_at
        interval = max(schedule.frequency_interval or 1, 1)
        if schedule.frequency_type == PMSchedule.FREQ_DAILY:
            return at + timedelta(days=interval)
        if schedule.frequency_type == PMSchedule.FREQ_WEEKLY:
            return at + timedelta(weeks=interval)
        if schedule.frequency_type == PMSchedule.FREQ_MONTHLY:
            return at + timedelta(days=30 * interval)
        if schedule.frequency_type == PMSchedule.FREQ_QUARTERLY:
            return at + timedelta(days=90 * interval)
        if schedule.frequency_type == PMSchedule.FREQ_YEARLY:
            return at + timedelta(days=365 * interval)
        return at + timedelta(days=interval)

    @transaction.atomic
    def run(self, *, actor: User | None = None, now: datetime | None = None) -> dict:
        current = now or timezone.now()
        summary = {
            "schedules_processed": 0,
            "tasks_created": 0,
            "skipped_duplicates": 0,
            "errors": 0,
        }
        for schedule in self.schedule_repository.get_due_schedules(now=current):
            summary["schedules_processed"] += 1
            try:
                if schedule.end_date and current.date() > schedule.end_date:
                    schedule.is_active = False
                    self.schedule_repository.save(schedule, update_fields=["is_active", "updated_at"])
                    continue
                if self.task_repository.exists_active_for_pm_schedule(schedule_id=schedule.id):
                    summary["skipped_duplicates"] += 1
                    schedule.last_run_at = current
                    schedule.next_run_at = self._compute_next_run(schedule, base=schedule.next_run_at)
                    self.schedule_repository.save(schedule, update_fields=["last_run_at", "next_run_at", "updated_at"])
                    continue
                task = self.maintenance_service.create_task(
                    reported_by=actor or schedule.created_by,
                    org_id=schedule.asset.org_id,
                    task_type=MaintenanceTask.TYPE_PREVENTIVE,
                    title=schedule.title,
                    description=schedule.description,
                    asset_id=schedule.asset_id,
                    room_id=schedule.asset.room_id,
                    property_id=schedule.asset.property_id,
                    department_id=schedule.asset.department_id,
                    priority=schedule.priority,
                    scheduled_at=current,
                    due_at=current,
                    pm_schedule_id=schedule.id,
                )
                summary["tasks_created"] += 1
                if task and schedule.asset.status == Asset.STATUS_ACTIVE:
                    schedule.asset.status = Asset.STATUS_UNDER_MAINTENANCE
                    schedule.asset.save(update_fields=["status", "updated_at"])
                schedule.last_run_at = current
                schedule.next_run_at = self._compute_next_run(schedule, base=schedule.next_run_at)
                self.schedule_repository.save(schedule, update_fields=["last_run_at", "next_run_at", "updated_at"])
            except Exception:
                summary["errors"] += 1
        return summary


class MaintenanceLogbookService:
    def __init__(
        self,
        *,
        repository: MaintenanceLogbookRepository | None = None,
        cost_calculator: MaintenanceCostCalculator | None = None,
    ) -> None:
        self.repository = repository or MaintenanceLogbookRepository()
        self.cost_calculator = cost_calculator or MaintenanceCostCalculator()

    @transaction.atomic
    def add_entry(
        self,
        *,
        task: MaintenanceTask,
        actor: User,
        entry_type: str,
        description: str,
        parts: list[dict] | None = None,
        labor: list[dict] | None = None,
    ) -> MaintenanceLogbookEntry:
        entry = self.repository.create_entry(
            maintenance_task=task,
            asset_id=task.asset_id,
            entry_type=entry_type,
            description=description,
            created_by=actor,
        )
        for part in parts or []:
            quantity = self.cost_calculator.norm(part.get("quantity"), "quantity")
            unit_cost = self.cost_calculator.norm(part.get("unit_cost"), "unit_cost")
            total = (quantity * unit_cost).quantize(Decimal("0.01"))
            MaintenancePartEntry.objects.create(
                logbook_entry=entry,
                part_name=part["part_name"],
                part_number=part.get("part_number", ""),
                quantity=quantity,
                unit_cost=unit_cost,
                total_cost=total,
            )
        for labor_row in labor or []:
            hours = self.cost_calculator.norm(labor_row.get("hours"), "hours")
            hourly_rate = self.cost_calculator.norm(labor_row.get("hourly_rate"), "hourly_rate")
            total_labor_cost = (hours * hourly_rate).quantize(Decimal("0.01"))
            MaintenanceLaborEntry.objects.create(
                logbook_entry=entry,
                technician_id=labor_row["technician_id"],
                hours=hours,
                hourly_rate=hourly_rate,
                total_labor_cost=total_labor_cost,
            )
        self.update_task_costs(task=task)
        return entry

    def list_entries(self, *, task_id: int) -> QuerySet[MaintenanceLogbookEntry]:
        return self.repository.list_for_task(task_id=task_id)

    @transaction.atomic
    def update_task_costs(self, *, task: MaintenanceTask) -> MaintenanceTask:
        totals = self.cost_calculator.compute_task_totals(task)
        task.parts_total = totals["parts_total"]
        task.labor_total = totals["labor_total"]
        task.total_cost = totals["grand_total"]
        task.save(update_fields=["parts_total", "labor_total", "total_cost", "updated_at"])
        return task

    def has_completion_summary(self, *, task: MaintenanceTask) -> bool:
        return MaintenanceLogbookEntry.objects.filter(
            maintenance_task=task,
            entry_type=MaintenanceLogbookEntry.TYPE_COMPLETION_SUMMARY,
        ).exists()


class QRAssetService:
    def __init__(
        self,
        *,
        asset_service: AssetService | None = None,
        maintenance_service: MaintenanceService | None = None,
    ) -> None:
        self.asset_service = asset_service or AssetService()
        self.maintenance_service = maintenance_service or MaintenanceService()

    def lookup(self, *, org_id: int, qr_code: str) -> Asset:
        return self.asset_service.asset_repository.get_by_qr_for_org(org_id=org_id, qr_code=qr_code)

    def lookup_with_context(self, *, org_id: int, qr_code: str) -> dict:
        asset = self.lookup(org_id=org_id, qr_code=qr_code)
        open_tasks = MaintenanceTask.objects.filter(
            asset=asset,
            status__in=[
                MaintenanceTask.STATUS_OPEN,
                MaintenanceTask.STATUS_ASSIGNED,
                MaintenanceTask.STATUS_IN_PROGRESS,
                MaintenanceTask.STATUS_ON_HOLD,
            ],
        ).order_by("-created_at")[:10]
        recent_entries = MaintenanceLogbookEntry.objects.filter(asset=asset).order_by("-created_at")[:10]
        return {
            "asset": asset,
            "open_tasks": list(open_tasks),
            "recent_entries": list(recent_entries),
        }

    @transaction.atomic
    def create_task_from_qr(self, *, org_id: int, qr_code: str, reported_by: User, **payload) -> MaintenanceTask:
        asset = self.lookup(org_id=org_id, qr_code=qr_code)
        return self.maintenance_service.create_task(
            reported_by=reported_by,
            org_id=org_id,
            task_type=MaintenanceTask.TYPE_CORRECTIVE,
            title=payload["title"],
            description=payload.get("description", ""),
            priority=payload.get("priority", MaintenanceTask.PRIORITY_MEDIUM),
            asset_id=asset.id,
            room_id=asset.room_id,
            property_id=asset.property_id,
            department_id=asset.department_id,
            due_at=payload.get("due_at"),
            scheduled_at=payload.get("scheduled_at"),
        )
