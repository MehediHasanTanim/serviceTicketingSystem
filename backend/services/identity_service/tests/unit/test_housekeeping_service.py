from datetime import timedelta

import pytest
from django.utils import timezone

from application.services.housekeeping import HousekeepingService, KPIService, TaskAssignmentService, TaskGenerationService
from infrastructure.db.core.models import AuditLog, HousekeepingTask, HousekeepingTaskAssignmentHistory, Room, RoomStatus, RoomStatusHistory, UserProperty
from tests.unit.api_test_helpers import create_org, create_user


def _mk_room(org, room_number="101", room_type="standard"):
    prop = org.properties.create(code="P1", name="Property", timezone="UTC", address_line1="a", city="c", country="x")
    floor = prop.buildings.create(name="B1").floors.create(level_number=1)
    room = Room.objects.create(property=prop, floor=floor, room_number=room_number, room_type=room_type, status="available")
    return room, prop


@pytest.mark.django_db
@pytest.mark.unit
def test_room_status_history_and_invalid_transition():
    org = create_org("HK Org")
    user = create_user(org, email="hk@example.com")
    room, _ = _mk_room(org)

    svc = HousekeepingService()
    svc.upsert_room_status(room=room, occupancy_status="VACANT", housekeeping_status="DIRTY", priority="MEDIUM", updated_by=user)
    svc.upsert_room_status(room=room, occupancy_status="VACANT", housekeeping_status="CLEAN", priority="HIGH", updated_by=user, reason="cleaned")

    history = RoomStatusHistory.objects.filter(room=room).order_by("id")
    assert history.count() == 2
    assert history.last().previous_occupancy_status == "VACANT"
    assert history.last().new_housekeeping_status == "CLEAN"

    with pytest.raises(Exception):
        svc.upsert_room_status(room=room, occupancy_status="OUT_OF_ORDER", housekeeping_status="READY", priority="HIGH", updated_by=user)


@pytest.mark.django_db
@pytest.mark.unit
def test_task_generation_rules_and_no_duplicate_active_task_and_cleaning_completion_inspection():
    org = create_org("HK Org")
    room, _ = _mk_room(org, room_number="102", room_type="VIP Suite")
    status_row = RoomStatus.objects.create(room=room, occupancy_status="VACANT", housekeeping_status="DIRTY", priority="HIGH")

    svc = TaskGenerationService()
    first = svc.generate_for_room(room_status=status_row, early_checkin=True)
    second = svc.generate_for_room(room_status=status_row, early_checkin=True)
    assert len(first) == 1
    assert first[0].task_type == "CLEANING"
    assert first[0].priority == "URGENT"
    assert len(second) == 0

    clean = first[0]
    clean.status = "COMPLETED"
    clean.save(update_fields=["status"])
    generated = svc.generate_post_completion_tasks(task=clean)
    assert len(generated) == 1
    assert generated[0].task_type == "INSPECTION"


@pytest.mark.django_db
@pytest.mark.unit
def test_long_stay_occupied_generates_periodic_cleaning():
    org = create_org("HK Org")
    room, _ = _mk_room(org, room_number="103")
    status_row = RoomStatus.objects.create(room=room, occupancy_status="OCCUPIED", housekeeping_status="DIRTY", priority="MEDIUM")
    RoomStatus.objects.filter(id=status_row.id).update(updated_at=timezone.now() - timedelta(days=5))
    status_row.refresh_from_db()

    svc = TaskGenerationService()
    created = svc.generate_for_room(room_status=status_row)
    assert any(t.task_type == "CLEANING" for t in created)


@pytest.mark.django_db
@pytest.mark.unit
def test_assignment_algorithms_and_reassignment_history():
    org = create_org("HK Org")
    room1, prop = _mk_room(org, room_number="201")
    room2, _ = _mk_room(org, room_number="202")
    room3, _ = _mk_room(org, room_number="203")

    active1 = create_user(org, email="a1@example.com", status="active")
    active2 = create_user(org, email="a2@example.com", status="active")
    suspended = create_user(org, email="s1@example.com", status="suspended")
    UserProperty.objects.create(user=active1, property=prop)
    UserProperty.objects.create(user=active2, property=prop)
    UserProperty.objects.create(user=suspended, property=prop)

    due = timezone.now() + timedelta(hours=1)
    t1 = HousekeepingTask.objects.create(room=room1, task_type="CLEANING", priority="MEDIUM", status="PENDING", due_at=due)
    t2 = HousekeepingTask.objects.create(room=room2, task_type="CLEANING", priority="MEDIUM", status="PENDING", due_at=due)
    t3 = HousekeepingTask.objects.create(room=room3, task_type="CLEANING", priority="MEDIUM", status="PENDING", due_at=due)

    assigner = TaskAssignmentService()
    assert assigner.assign_round_robin(org_id=org.id, property_id=prop.id, changed_by=active1) == 3
    assert HousekeepingTask.objects.filter(assigned_to=suspended).count() == 0

    extra = HousekeepingTask.objects.create(room=room1, task_type="INSPECTION", priority="MEDIUM", status="PENDING", due_at=due)
    assert assigner.assign_least_loaded(org_id=org.id, property_id=prop.id, changed_by=active1) == 1
    extra.refresh_from_db()
    assert extra.assigned_to_id in {active1.id, active2.id}

    t1.refresh_from_db()
    re = assigner.reassign_task(task=t1, assignee=active2, changed_by=active1, reason="balance")
    assert re.assigned_to_id == active2.id
    assert HousekeepingTaskAssignmentHistory.objects.filter(task=t1).count() >= 2


@pytest.mark.django_db
@pytest.mark.unit
def test_kpi_aggregation_and_zero_safe():
    org = create_org("HK Org")
    room, _ = _mk_room(org, room_number="301", room_type="suite")
    staff = create_user(org, email="staff@example.com", status="active")

    now = timezone.now()
    HousekeepingTask.objects.create(room=room, task_type="CLEANING", priority="MEDIUM", status="PENDING", due_at=now - timedelta(hours=1))
    done = HousekeepingTask.objects.create(room=room, task_type="INSPECTION", priority="MEDIUM", status="COMPLETED", due_at=now + timedelta(hours=1), assigned_to=staff)
    done.created_at = now - timedelta(hours=2)
    done.updated_at = now - timedelta(hours=1)
    done.save(update_fields=["created_at", "updated_at"])

    RoomStatusHistory.objects.create(room=room, previous_occupancy_status="VACANT", new_occupancy_status="VACANT", previous_housekeeping_status="DIRTY", new_housekeeping_status="CLEAN", changed_by=staff)

    svc = KPIService()
    summary = svc.summary(org_id=org.id)
    assert summary["total_tasks_created"] == 2
    assert summary["total_tasks_completed"] == 1
    assert summary["overdue_tasks_count"] == 1

    staff_perf = svc.staff_performance(org_id=org.id)
    assert staff_perf[0]["tasks_completed"] == 1

    turnaround = svc.room_turnaround(org_id=org.id)
    assert turnaround["events"] == 1

    empty_org = create_org("Empty")
    assert svc.summary(org_id=empty_org.id)["total_tasks_created"] == 0
