from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, QuerySet
from django.utils import timezone

from infrastructure.db.core.models import (
    HousekeepingTask,
    HousekeepingTaskAssignmentHistory,
    PMSSyncLog,
    Room,
    RoomStatus,
    RoomStatusHistory,
    User,
)


class HousekeepingError(Exception):
    pass


class HousekeepingValidationError(HousekeepingError):
    pass


class HousekeepingNotFoundError(HousekeepingError):
    pass


@dataclass
class TaskGenerationConfig:
    long_stay_days: int = 3


class RoomStatusRepository:
    def get_for_room(self, room_id: int) -> RoomStatus:
        try:
            return RoomStatus.objects.select_related("room").get(room_id=room_id)
        except RoomStatus.DoesNotExist as exc:
            raise HousekeepingNotFoundError("Room status not found") from exc

    def list_for_property(self, property_id: int) -> QuerySet[RoomStatus]:
        return RoomStatus.objects.select_related("room").filter(room__property_id=property_id)

    def create(self, **kwargs) -> RoomStatus:
        return RoomStatus.objects.create(**kwargs)

    def save(self, room_status: RoomStatus, *, update_fields: list[str] | None = None) -> RoomStatus:
        room_status.save(update_fields=update_fields)
        return room_status


class RoomStatusHistoryRepository:
    def create(
        self,
        *,
        room: Room,
        previous_occupancy_status: str,
        new_occupancy_status: str,
        previous_housekeeping_status: str,
        new_housekeeping_status: str,
        changed_by: User | None,
        reason: str = "",
    ) -> RoomStatusHistory:
        return RoomStatusHistory.objects.create(
            room=room,
            previous_occupancy_status=previous_occupancy_status,
            new_occupancy_status=new_occupancy_status,
            previous_housekeeping_status=previous_housekeeping_status,
            new_housekeeping_status=new_housekeeping_status,
            changed_by=changed_by,
            reason=reason,
        )


class HousekeepingTaskRepository:
    def create(self, **kwargs) -> HousekeepingTask:
        return HousekeepingTask.objects.create(**kwargs)

    def list_open_for_room(self, room_id: int, task_type: str) -> QuerySet[HousekeepingTask]:
        return HousekeepingTask.objects.filter(
            room_id=room_id,
            task_type=task_type,
            status__in=[
                HousekeepingTask.STATUS_PENDING,
                HousekeepingTask.STATUS_ASSIGNED,
                HousekeepingTask.STATUS_IN_PROGRESS,
            ],
        )

    def list_unassigned(self, property_id: int) -> QuerySet[HousekeepingTask]:
        return HousekeepingTask.objects.select_related("room").filter(
            room__property_id=property_id,
            assigned_to__isnull=True,
            status=HousekeepingTask.STATUS_PENDING,
        )


class HousekeepingService:
    INVALID_COMBINATIONS = {
        (RoomStatus.OCCUPANCY_OUT_OF_ORDER, RoomStatus.HK_READY),
        (RoomStatus.OCCUPANCY_OUT_OF_ORDER, RoomStatus.HK_CLEAN),
        (RoomStatus.OCCUPANCY_RESERVED, RoomStatus.HK_BLOCKED),
    }

    def __init__(
        self,
        *,
        room_status_repository: RoomStatusRepository | None = None,
        room_status_history_repository: RoomStatusHistoryRepository | None = None,
    ) -> None:
        self.room_status_repository = room_status_repository or RoomStatusRepository()
        self.room_status_history_repository = room_status_history_repository or RoomStatusHistoryRepository()

    @transaction.atomic
    def upsert_room_status(
        self,
        *,
        room: Room,
        occupancy_status: str,
        housekeeping_status: str,
        priority: str,
        updated_by: User | None,
        reason: str = "",
    ) -> RoomStatus:
        if (occupancy_status, housekeeping_status) in self.INVALID_COMBINATIONS:
            raise HousekeepingValidationError("Invalid occupancy/housekeeping status combination")

        existing = RoomStatus.objects.filter(room=room).first()
        if not existing:
            status = self.room_status_repository.create(
                room=room,
                occupancy_status=occupancy_status,
                housekeeping_status=housekeeping_status,
                priority=priority,
                updated_by=updated_by,
            )
            self.room_status_history_repository.create(
                room=room,
                previous_occupancy_status=occupancy_status,
                new_occupancy_status=occupancy_status,
                previous_housekeeping_status=housekeeping_status,
                new_housekeeping_status=housekeeping_status,
                changed_by=updated_by,
                reason=reason or "Initial status",
            )
            return status

        prev_occ = existing.occupancy_status
        prev_hk = existing.housekeeping_status

        existing.occupancy_status = occupancy_status
        existing.housekeeping_status = housekeeping_status
        existing.priority = priority
        existing.updated_by = updated_by
        self.room_status_repository.save(existing)

        if prev_occ != occupancy_status or prev_hk != housekeeping_status:
            self.room_status_history_repository.create(
                room=room,
                previous_occupancy_status=prev_occ,
                new_occupancy_status=occupancy_status,
                previous_housekeeping_status=prev_hk,
                new_housekeeping_status=housekeeping_status,
                changed_by=updated_by,
                reason=reason,
            )
        return existing


class TaskGenerationService:
    def __init__(
        self,
        *,
        task_repository: HousekeepingTaskRepository | None = None,
        config: TaskGenerationConfig | None = None,
    ) -> None:
        self.task_repository = task_repository or HousekeepingTaskRepository()
        self.config = config or TaskGenerationConfig()

    def _priority(self, room_status: RoomStatus, *, early_checkin: bool = False) -> str:
        room_type = (room_status.room.room_type or "").lower()
        if "vip" in room_type:
            return HousekeepingTask.PRIORITY_HIGH
        if early_checkin:
            return HousekeepingTask.PRIORITY_URGENT
        return HousekeepingTask.PRIORITY_MEDIUM

    @transaction.atomic
    def generate_for_room(
        self,
        *,
        room_status: RoomStatus,
        due_at: datetime | None = None,
        notes: str = "",
        early_checkin: bool = False,
    ) -> list[HousekeepingTask]:
        due = due_at or (timezone.now() + timedelta(hours=2))
        created: list[HousekeepingTask] = []

        def ensure_task(task_type: str, priority: str):
            if self.task_repository.list_open_for_room(room_status.room_id, task_type).exists():
                return
            created.append(
                self.task_repository.create(
                    room=room_status.room,
                    task_type=task_type,
                    priority=priority,
                    status=HousekeepingTask.STATUS_PENDING,
                    due_at=due,
                    notes=notes,
                )
            )

        priority = self._priority(room_status, early_checkin=early_checkin)

        if room_status.occupancy_status == RoomStatus.OCCUPANCY_VACANT and room_status.housekeeping_status == RoomStatus.HK_DIRTY:
            ensure_task(HousekeepingTask.TYPE_CLEANING, priority)

        if room_status.occupancy_status == RoomStatus.OCCUPANCY_OCCUPIED:
            threshold = timezone.now() - timedelta(days=self.config.long_stay_days)
            if not room_status.updated_at or room_status.updated_at <= threshold:
                ensure_task(HousekeepingTask.TYPE_CLEANING, HousekeepingTask.PRIORITY_MEDIUM)

        if room_status.occupancy_status == RoomStatus.OCCUPANCY_OUT_OF_ORDER or room_status.housekeeping_status == RoomStatus.HK_BLOCKED:
            ensure_task(HousekeepingTask.TYPE_MAINTENANCE_SUPPORT, HousekeepingTask.PRIORITY_HIGH)

        return created

    @transaction.atomic
    def generate_post_completion_tasks(self, *, task: HousekeepingTask, actor: User | None = None) -> list[HousekeepingTask]:
        if task.task_type != HousekeepingTask.TYPE_CLEANING or task.status != HousekeepingTask.STATUS_COMPLETED:
            return []
        if self.task_repository.list_open_for_room(task.room_id, HousekeepingTask.TYPE_INSPECTION).exists():
            return []
        inspection = self.task_repository.create(
            room=task.room,
            task_type=HousekeepingTask.TYPE_INSPECTION,
            priority=task.priority,
            status=HousekeepingTask.STATUS_PENDING,
            due_at=timezone.now() + timedelta(hours=1),
            notes="Auto-generated after cleaning completion",
            created_by=actor,
        )
        return [inspection]

    @transaction.atomic
    def generate_batch(self, *, room_statuses: QuerySet[RoomStatus]) -> int:
        total = 0
        for row in room_statuses.select_related("room"):
            total += len(self.generate_for_room(room_status=row))
        return total


class TaskAssignmentService:
    def __init__(self, *, task_repository: HousekeepingTaskRepository | None = None) -> None:
        self.task_repository = task_repository or HousekeepingTaskRepository()

    def _available_staff(self, org_id: int, property_id: int) -> QuerySet[User]:
        return User.objects.filter(
            org_id=org_id,
            status="active",
            user_properties__property_id=property_id,
        ).distinct().order_by("id")

    def _is_assignable(self, task: HousekeepingTask) -> bool:
        return task.status not in {HousekeepingTask.STATUS_COMPLETED, HousekeepingTask.STATUS_CANCELLED}

    @transaction.atomic
    def assign_round_robin(self, *, org_id: int, property_id: int, changed_by: User | None = None) -> int:
        staff = list(self._available_staff(org_id, property_id))
        if not staff:
            return 0
        tasks = [t for t in self.task_repository.list_unassigned(property_id) if self._is_assignable(t)]
        if not tasks:
            return 0

        assigned = 0
        for idx, task in enumerate(tasks):
            assignee = staff[idx % len(staff)]
            task.assigned_to = assignee
            task.status = HousekeepingTask.STATUS_ASSIGNED
            task.save(update_fields=["assigned_to", "status", "updated_at"])
            HousekeepingTaskAssignmentHistory.objects.create(
                task=task,
                previous_assignee=None,
                new_assignee=assignee,
                changed_by=changed_by,
                reason="round_robin",
            )
            assigned += 1
        return assigned

    @transaction.atomic
    def assign_least_loaded(self, *, org_id: int, property_id: int, changed_by: User | None = None) -> int:
        staff = list(self._available_staff(org_id, property_id))
        if not staff:
            return 0

        load_map = {
            user.id: HousekeepingTask.objects.filter(
                assigned_to=user,
                status__in=[HousekeepingTask.STATUS_ASSIGNED, HousekeepingTask.STATUS_IN_PROGRESS],
            ).count()
            for user in staff
        }

        assigned = 0
        for task in self.task_repository.list_unassigned(property_id):
            if not self._is_assignable(task):
                continue
            assignee_id = min(load_map, key=lambda uid: load_map[uid])
            assignee = next(u for u in staff if u.id == assignee_id)
            task.assigned_to = assignee
            task.status = HousekeepingTask.STATUS_ASSIGNED
            task.save(update_fields=["assigned_to", "status", "updated_at"])
            load_map[assignee_id] += 1
            HousekeepingTaskAssignmentHistory.objects.create(
                task=task,
                previous_assignee=None,
                new_assignee=assignee,
                changed_by=changed_by,
                reason="least_loaded",
            )
            assigned += 1
        return assigned

    @transaction.atomic
    def reassign_task(self, *, task: HousekeepingTask, assignee: User, changed_by: User | None, reason: str) -> HousekeepingTask:
        if not self._is_assignable(task):
            raise HousekeepingValidationError("Task cannot be assigned in current status")
        if task.assigned_to_id == assignee.id and not reason:
            raise HousekeepingValidationError("Reason required for assigning task to same user")
        previous = task.assigned_to
        task.assigned_to = assignee
        task.status = HousekeepingTask.STATUS_ASSIGNED
        task.save(update_fields=["assigned_to", "status", "updated_at"])
        HousekeepingTaskAssignmentHistory.objects.create(
            task=task,
            previous_assignee=previous,
            new_assignee=assignee,
            changed_by=changed_by,
            reason=reason,
        )
        return task

    @transaction.atomic
    def reassign_overdue(self, *, org_id: int, property_id: int, changed_by: User | None = None) -> int:
        staff = list(self._available_staff(org_id, property_id))
        if not staff:
            return 0
        overdue = HousekeepingTask.objects.filter(
            room__property_id=property_id,
            due_at__lt=timezone.now(),
            status__in=[HousekeepingTask.STATUS_ASSIGNED, HousekeepingTask.STATUS_IN_PROGRESS],
        ).exclude(assigned_to__isnull=True)
        count = 0
        for task in overdue:
            candidates = [u for u in staff if u.id != task.assigned_to_id]
            if not candidates:
                continue
            self.reassign_task(task=task, assignee=candidates[0], changed_by=changed_by, reason="overdue_reassignment")
            count += 1
        return count


class KPIService:
    def _base_tasks(self, *, org_id: int, date_from=None, date_to=None, property_id=None, floor_id=None, room_type=None, staff_id=None):
        tasks = HousekeepingTask.objects.filter(room__property__org_id=org_id)
        if date_from:
            tasks = tasks.filter(created_at__gte=date_from)
        if date_to:
            tasks = tasks.filter(created_at__lte=date_to)
        if property_id:
            tasks = tasks.filter(room__property_id=property_id)
        if floor_id:
            tasks = tasks.filter(room__floor_id=floor_id)
        if room_type:
            tasks = tasks.filter(room__room_type=room_type)
        if staff_id:
            tasks = tasks.filter(assigned_to_id=staff_id)
        return tasks

    def summary(self, *, org_id: int, date_from: datetime | None = None, date_to: datetime | None = None, property_id: int | None = None, floor_id: int | None = None, staff_id: int | None = None, room_type: str | None = None) -> dict:
        tasks = self._base_tasks(org_id=org_id, date_from=date_from, date_to=date_to, property_id=property_id, floor_id=floor_id, room_type=room_type, staff_id=staff_id)
        completed = tasks.filter(status=HousekeepingTask.STATUS_COMPLETED)
        avg_completion = completed.aggregate(
            value=Avg(ExpressionWrapper(F("updated_at") - F("created_at"), output_field=DurationField()))
        )["value"]

        overdue = tasks.filter(
            due_at__lt=timezone.now(),
            status__in=[HousekeepingTask.STATUS_PENDING, HousekeepingTask.STATUS_ASSIGNED, HousekeepingTask.STATUS_IN_PROGRESS],
        ).count()

        sla_total = completed.count()
        sla_hit = completed.filter(updated_at__lte=F("due_at")).count() if sla_total else 0

        return {
            "total_tasks_created": tasks.count(),
            "total_tasks_completed": sla_total,
            "pending_tasks_count": tasks.filter(status=HousekeepingTask.STATUS_PENDING).count(),
            "overdue_tasks_count": overdue,
            "average_completion_time": avg_completion,
            "sla_compliance_percentage": float((sla_hit / sla_total) * 100) if sla_total else 0.0,
        }

    def staff_performance(self, *, org_id: int, date_from: datetime | None = None, date_to: datetime | None = None, property_id: int | None = None, floor_id: int | None = None, room_type: str | None = None, staff_id: int | None = None) -> list[dict]:
        qs = self._base_tasks(org_id=org_id, date_from=date_from, date_to=date_to, property_id=property_id, floor_id=floor_id, room_type=room_type, staff_id=staff_id).filter(
            status=HousekeepingTask.STATUS_COMPLETED,
            assigned_to__isnull=False,
        )
        rows = qs.values("assigned_to_id").annotate(total=Count("id")).order_by("-total")
        return [{"staff_id": row["assigned_to_id"], "tasks_completed": row["total"]} for row in rows]

    def room_turnaround(self, *, org_id: int, date_from: datetime | None = None, date_to: datetime | None = None, property_id: int | None = None, floor_id: int | None = None, room_type: str | None = None, staff_id: int | None = None) -> dict:
        histories = RoomStatusHistory.objects.filter(room__property__org_id=org_id)
        if date_from:
            histories = histories.filter(changed_at__gte=date_from)
        if date_to:
            histories = histories.filter(changed_at__lte=date_to)
        if property_id:
            histories = histories.filter(room__property_id=property_id)
        if floor_id:
            histories = histories.filter(room__floor_id=floor_id)
        if room_type:
            histories = histories.filter(room__room_type=room_type)
        if staff_id:
            histories = histories.filter(changed_by_id=staff_id)

        return {
            "events": histories.count(),
            "average_room_turnaround_time": histories.aggregate(value=Avg("changed_at"))["value"],
        }


class PMSSyncService:
    @transaction.atomic
    def sync_room_status(
        self,
        *,
        room: Room,
        external_reference_id: str,
        occupancy_status: str,
        housekeeping_status: str,
        timestamp: datetime,
        updated_by: User | None,
        idempotency_key: str = "",
        reason: str = "pms_sync",
    ) -> RoomStatus:
        event_key = idempotency_key or external_reference_id or f"room-status:{room.id}:{timestamp.isoformat()}"
        log, created = PMSSyncLog.objects.get_or_create(
            source="pms_room_status",
            event_key=event_key,
            defaults={
                "payload_json": {
                    "external_reference_id": external_reference_id,
                    "room_id": room.id,
                    "occupancy_status": occupancy_status,
                    "housekeeping_status": housekeeping_status,
                    "timestamp": timestamp.isoformat(),
                },
                "external_reference_id": external_reference_id,
                "status": "SUCCESS",
            },
        )
        if not created:
            status = RoomStatus.objects.filter(room=room).first()
            if status:
                return status

        svc = HousekeepingService()
        status = svc.upsert_room_status(
            room=room,
            occupancy_status=occupancy_status,
            housekeeping_status=housekeeping_status,
            priority=RoomStatus.PRIORITY_MEDIUM,
            updated_by=updated_by,
            reason=reason,
        )
        log.status = "SUCCESS"
        log.save(update_fields=["status"])
        return status

    def pull_room_status(self, *, property_id: int | None = None) -> QuerySet[RoomStatus]:
        qs = RoomStatus.objects.select_related("room")
        if property_id:
            qs = qs.filter(room__property_id=property_id)
        return qs

    @transaction.atomic
    def sync_task_update(
        self,
        *,
        task: HousekeepingTask,
        status_value: str,
        timestamp: datetime,
        external_reference_id: str = "",
        idempotency_key: str = "",
    ) -> HousekeepingTask:
        event_key = idempotency_key or external_reference_id or f"task-status:{task.id}:{status_value}:{timestamp.isoformat()}"
        created = PMSSyncLog.objects.get_or_create(
            source="pms_housekeeping_task",
            event_key=event_key,
            defaults={
                "payload_json": {"task_id": task.id, "status": status_value, "timestamp": timestamp.isoformat()},
                "external_reference_id": external_reference_id,
                "status": "SUCCESS",
            },
        )[1]
        if not created:
            return task
        task.status = status_value
        task.save(update_fields=["status", "updated_at"])
        return task
