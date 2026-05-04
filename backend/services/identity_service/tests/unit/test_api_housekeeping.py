import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from infrastructure.db.core.models import AuditLog, HousekeepingTask, PMSSyncLog, Room
from tests.unit.api_test_helpers import authenticated_client, create_org, create_user, grant_permissions


def _make_room(org):
    prop = org.properties.create(code="P1", name="Property", timezone="UTC", address_line1="a", city="c", country="x")
    floor = prop.buildings.create(name="B1").floors.create(level_number=1)
    room = Room.objects.create(property=prop, floor=floor, room_number="401", room_type="VIP", status="available")
    return room, prop


@pytest.mark.django_db
@pytest.mark.unit
def test_api_room_status_task_generation_and_kpi_envelope_and_audit():
    org = create_org("HK API")
    actor = create_user(org, email="actor@example.com")
    grant_permissions(actor, ["housekeeping.manage", "housekeeping.view"], role_name="housekeeping")
    client = authenticated_client(actor)

    room, prop = _make_room(org)

    upsert = client.post(
        reverse("housekeeping-room-status"),
        {"room_id": room.id, "occupancy_status": "VACANT", "housekeeping_status": "DIRTY", "priority": "HIGH", "reason": "checkout"},
        format="json",
    )
    assert upsert.status_code == status.HTTP_200_OK
    assert upsert.data["data"]["occupancy_status"] == "VACANT"

    gen = client.post(reverse("housekeeping-task-generate"), {"property_id": prop.id}, format="json")
    assert gen.status_code == status.HTTP_200_OK
    assert gen.data["data"]["created_tasks"] == 1

    summary = client.get(reverse("housekeeping-kpi-summary"), {"org_id": org.id, "property_id": prop.id})
    assert summary.status_code == status.HTTP_200_OK
    assert "data" in summary.data

    assert AuditLog.objects.filter(action="room_status_changed").exists()
    assert AuditLog.objects.filter(action="housekeeping_task_generated").exists()


@pytest.mark.django_db
@pytest.mark.unit
def test_pms_sync_payload_idempotency_and_audit_failure_log():
    org = create_org("HK API")
    room, _ = _make_room(org)
    client = authenticated_client(create_user(org, email="viewer@example.com"))

    ts = timezone.now().replace(microsecond=0)
    payload = {
        "external_reference_id": f"PMS-ROOM-{room.id}",
        "room_id": room.id,
        "occupancy_status": "VACANT",
        "housekeeping_status": "DIRTY",
        "timestamp": ts.isoformat(),
    }
    ok1 = client.post(reverse("pms-room-status-sync"), payload, format="json", HTTP_IDEMPOTENCY_KEY="k1")
    ok2 = client.post(reverse("pms-room-status-sync"), payload, format="json", HTTP_IDEMPOTENCY_KEY="k1")
    assert ok1.status_code == status.HTTP_200_OK
    assert ok2.status_code == status.HTTP_200_OK
    assert PMSSyncLog.objects.filter(source="pms_room_status", event_key="k1").count() == 1

    invalid = client.post(reverse("pms-room-status-sync"), {"room_id": room.id}, format="json")
    assert invalid.status_code == status.HTTP_400_BAD_REQUEST

    task = HousekeepingTask.objects.create(room=room, task_type="CLEANING", priority="MEDIUM", status="PENDING", due_at=timezone.now())
    task_sync = client.post(
        reverse("pms-housekeeping-task-sync"),
        {"external_reference_id": "PMS-TASK-1", "task_id": task.id, "status": "COMPLETED", "timestamp": ts.isoformat()},
        format="json",
        HTTP_IDEMPOTENCY_KEY="kt1",
    )
    assert task_sync.status_code == status.HTTP_200_OK
    task.refresh_from_db()
    assert task.status == "COMPLETED"

    assert AuditLog.objects.filter(action="pms_sync_received").exists()


@pytest.mark.django_db
@pytest.mark.unit
def test_housekeeping_task_list_detail_and_lifecycle_endpoints():
    org = create_org("HK Tasks API")
    actor = create_user(org, email="hk-manager@example.com")
    assignee = create_user(org, email="hk-staff@example.com")
    grant_permissions(actor, ["housekeeping.manage", "housekeeping.view"], role_name="housekeeping")
    client = authenticated_client(actor)
    room, _ = _make_room(org)

    task = HousekeepingTask.objects.create(
        room=room,
        task_type="CLEANING",
        priority="HIGH",
        status="ASSIGNED",
        assigned_to=assignee,
        due_at=timezone.now(),
    )

    list_res = client.get(reverse("housekeeping-task-list"), {"org_id": org.id, "status": "ASSIGNED"})
    assert list_res.status_code == status.HTTP_200_OK
    assert list_res.data["count"] >= 1

    detail_res = client.get(reverse("housekeeping-task-detail", kwargs={"task_id": task.id}), {"org_id": org.id})
    assert detail_res.status_code == status.HTTP_200_OK
    assert detail_res.data["data"]["id"] == task.id

    start_res = client.post(reverse("housekeeping-task-start", kwargs={"task_id": task.id}), {"org_id": org.id}, format="json")
    assert start_res.status_code == status.HTTP_200_OK
    assert start_res.data["data"]["status"] == "IN_PROGRESS"

    complete_res = client.post(
        reverse("housekeeping-task-complete", kwargs={"task_id": task.id}),
        {"org_id": org.id, "note": "Finished cleaning"},
        format="json",
    )
    assert complete_res.status_code == status.HTTP_200_OK
    assert complete_res.data["data"]["status"] == "COMPLETED"

    verify_res = client.post(
        reverse("housekeeping-task-verify", kwargs={"task_id": task.id}),
        {"org_id": org.id, "note": "Supervisor approved"},
        format="json",
    )
    assert verify_res.status_code == status.HTTP_200_OK
    assert verify_res.data["data"]["status"] == "COMPLETED"

    reopen_res = client.post(
        reverse("housekeeping-task-reopen", kwargs={"task_id": task.id}),
        {"org_id": org.id, "reason": "Guest reported issue"},
        format="json",
    )
    assert reopen_res.status_code == status.HTTP_200_OK
    assert reopen_res.data["data"]["status"] == "ASSIGNED"

    cancel_res = client.post(
        reverse("housekeeping-task-cancel", kwargs={"task_id": task.id}),
        {"org_id": org.id, "reason": "Cancelled by supervisor"},
        format="json",
    )
    assert cancel_res.status_code == status.HTTP_200_OK
    assert cancel_res.data["data"]["status"] == "CANCELLED"

    bad_complete = client.post(reverse("housekeeping-task-complete", kwargs={"task_id": task.id}), {"org_id": org.id}, format="json")
    assert bad_complete.status_code == status.HTTP_400_BAD_REQUEST

    actions = set(
        AuditLog.objects.filter(target_type="housekeeping_task", target_id=str(task.id)).values_list("action", flat=True)
    )
    assert "housekeeping_task_started" in actions
    assert "housekeeping_task_completed" in actions
    assert "housekeeping_task_verified" in actions
    assert "housekeeping_task_reopened" in actions
    assert "housekeeping_task_cancelled" in actions
