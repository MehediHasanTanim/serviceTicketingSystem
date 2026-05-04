from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from application.services.maintenance import (
    AssetService,
    MaintenanceLogbookService,
    MaintenanceService,
    MaintenanceTransitionError,
    MaintenanceValidationError,
    PMSchedulerService,
)
from infrastructure.db.core.models import Asset, AssetLifecycleHistory, MaintenanceTask, PMSchedule
from tests.unit.api_test_helpers import create_org, create_user


@pytest.mark.django_db
@pytest.mark.unit
def test_asset_lifecycle_valid_invalid_retired_terminal_and_history():
    org = create_org("Maint Org")
    actor = create_user(org, email="maint-actor@example.com")
    service = AssetService()
    asset = service.create_asset(created_by=actor, org_id=org.id, name="AC Unit")

    service.change_status(asset=asset, new_status=Asset.STATUS_UNDER_MAINTENANCE, changed_by=actor, reason="inspection")
    asset.refresh_from_db()
    assert asset.status == Asset.STATUS_UNDER_MAINTENANCE

    with pytest.raises(MaintenanceTransitionError):
        service.change_status(asset=asset, new_status=Asset.STATUS_INACTIVE, changed_by=actor)

    service.change_status(asset=asset, new_status=Asset.STATUS_RETIRED, changed_by=actor)
    with pytest.raises(MaintenanceTransitionError):
        service.change_status(asset=asset, new_status=Asset.STATUS_ACTIVE, changed_by=actor)

    assert AssetLifecycleHistory.objects.filter(asset=asset).count() >= 3


@pytest.mark.django_db
@pytest.mark.unit
def test_pm_scheduler_due_inactive_duplicate_next_run_summary_and_custom_interval():
    org = create_org("PM Org")
    actor = create_user(org, email="pm-actor@example.com")
    asset_service = AssetService()
    asset = asset_service.create_asset(created_by=actor, org_id=org.id, name="Boiler")

    now = timezone.now()
    due = PMSchedule.objects.create(
        asset=asset,
        title="Weekly Boiler Check",
        description="desc",
        frequency_type=PMSchedule.FREQ_WEEKLY,
        frequency_interval=1,
        next_run_at=now - timedelta(minutes=1),
        start_date=date.today(),
        priority=MaintenanceTask.PRIORITY_HIGH,
        is_active=True,
        created_by=actor,
    )
    PMSchedule.objects.create(
        asset=asset,
        title="Inactive",
        description="desc",
        frequency_type=PMSchedule.FREQ_DAILY,
        frequency_interval=1,
        next_run_at=now - timedelta(minutes=1),
        start_date=date.today(),
        priority=MaintenanceTask.PRIORITY_MEDIUM,
        is_active=False,
        created_by=actor,
    )
    custom = PMSchedule.objects.create(
        asset=asset,
        title="Custom",
        description="desc",
        frequency_type=PMSchedule.FREQ_CUSTOM,
        frequency_interval=2,
        next_run_at=now - timedelta(minutes=1),
        start_date=date.today(),
        priority=MaintenanceTask.PRIORITY_MEDIUM,
        is_active=True,
        created_by=actor,
    )

    scheduler = PMSchedulerService()
    first = scheduler.run(actor=actor, now=now)
    assert first["schedules_processed"] == 2
    assert first["tasks_created"] == 2
    assert first["errors"] == 0

    due.refresh_from_db()
    assert due.next_run_at >= now + timedelta(days=7)

    # force duplicate window
    due.next_run_at = now - timedelta(minutes=1)
    due.save(update_fields=["next_run_at", "updated_at"])
    second = scheduler.run(actor=actor, now=now)
    assert second["skipped_duplicates"] >= 1

    custom.refresh_from_db()
    assert custom.next_run_at >= now + timedelta(days=2)


@pytest.mark.django_db
@pytest.mark.unit
def test_logbook_parts_labor_negative_guard_totals_and_completion_summary_requirement():
    org = create_org("Logbook Org")
    actor = create_user(org, email="log-actor@example.com")
    tech = create_user(org, email="tech@example.com")

    asset = AssetService().create_asset(created_by=actor, org_id=org.id, name="Generator")
    task_service = MaintenanceService()
    task = task_service.create_task(
        reported_by=actor,
        org_id=org.id,
        task_type=MaintenanceTask.TYPE_CORRECTIVE,
        title="Fix generator",
        asset_id=asset.id,
    )

    logbook = MaintenanceLogbookService()
    entry = logbook.add_entry(
        task=task,
        actor=actor,
        entry_type="PART_USED",
        description="Replaced filter",
        parts=[{"part_name": "Filter", "part_number": "F-1", "quantity": "2", "unit_cost": "10.50"}],
    )
    assert entry.id is not None

    logbook.add_entry(
        task=task,
        actor=actor,
        entry_type="LABOR",
        description="Technician labor",
        labor=[{"technician_id": tech.id, "hours": "1.50", "hourly_rate": "20.00"}],
    )

    task.refresh_from_db()
    assert task.parts_total == Decimal("21.00")
    assert task.labor_total == Decimal("30.00")
    assert task.total_cost == Decimal("51.00")

    with pytest.raises(MaintenanceValidationError):
        logbook.add_entry(
            task=task,
            actor=actor,
            entry_type="PART_USED",
            description="bad",
            parts=[{"part_name": "bad", "quantity": "-1", "unit_cost": "2"}],
        )

    assert logbook.has_completion_summary(task=task) is False
    logbook.add_entry(task=task, actor=actor, entry_type="COMPLETION_SUMMARY", description="done")
    assert logbook.has_completion_summary(task=task) is True
