from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.services.audit_logging import AuditContext
from application.services.housekeeping import (
    HousekeepingService,
    HousekeepingValidationError,
    KPIService,
    PMSSyncService,
    TaskAssignmentService,
    TaskGenerationService,
)
from infrastructure.db.core.models import HousekeepingTask, PMSSyncLog, RolePermission, Room, RoomStatus, UserRole
from infrastructure.services.audit_logging import get_audit_logger
from interfaces.api.serializers import (
    HousekeepingAssignSerializer,
    HousekeepingTaskActionSerializer,
    HousekeepingTaskListFilterSerializer,
    HousekeepingKPIFilterSerializer,
    HousekeepingTaskSyncSerializer,
    PMSRoomStatusPullSerializer,
    PMSRoomStatusSyncSerializer,
    RoomStatusUpsertSerializer,
)


def _has_permission(user, code: str) -> bool:
    if not user:
        return False
    if hasattr(user, "is_authenticated") and not user.is_authenticated:
        return False
    if UserRole.objects.filter(user=user, role__name__iexact="super admin").exists():
        return True
    return RolePermission.objects.filter(role__user_roles__user=user, permission__code=code).exists()


def _audit_context(request, *, org_id: int, property_id=None, actor=None):
    return AuditContext(
        org_id=org_id,
        property_id=property_id,
        actor_user_id=getattr(actor, "id", None),
        ip_address=request.META.get("REMOTE_ADDR", ""),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )


def _audit(request, *, org_id: int, action: str, entity_type: str, entity_id: str, metadata: dict | None = None, property_id=None, actor=None):
    try:
        get_audit_logger().log_action(
            action=action,
            target_type=entity_type,
            target_id=entity_id,
            metadata=metadata or {},
            context=_audit_context(request, org_id=org_id, property_id=property_id, actor=actor),
        )
    except Exception:
        pass


def _room_status_to_dict(row: RoomStatus) -> dict:
    return {
        "id": row.id,
        "room_id": row.room_id,
        "occupancy_status": row.occupancy_status,
        "housekeeping_status": row.housekeeping_status,
        "priority": row.priority,
        "updated_at": row.updated_at,
        "updated_by": row.updated_by_id,
    }


def _task_to_dict(task: HousekeepingTask) -> dict:
    return {
        "id": task.id,
        "room_id": task.room_id,
        "task_type": task.task_type,
        "priority": task.priority,
        "status": task.status,
        "assigned_to": task.assigned_to_id,
        "due_at": task.due_at,
        "notes": task.notes,
        "created_by": task.created_by_id,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


class HousekeepingTaskListView(APIView):
    def get(self, request):
        if not _has_permission(request.user, "housekeeping.view"):
            return Response({"detail": "Permission required: housekeeping.view"}, status=status.HTTP_403_FORBIDDEN)

        serializer = HousekeepingTaskListFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        tasks = HousekeepingTask.objects.select_related("room").filter(room__property__org_id=data["org_id"])
        if data.get("property_id"):
            tasks = tasks.filter(room__property_id=data["property_id"])
        if data.get("floor_id"):
            tasks = tasks.filter(room__floor_id=data["floor_id"])
        if data.get("room_id"):
            tasks = tasks.filter(room_id=data["room_id"])
        if data.get("assigned_to"):
            tasks = tasks.filter(assigned_to_id=data["assigned_to"])
        if data.get("priority"):
            tasks = tasks.filter(priority=data["priority"])
        if data.get("task_type"):
            tasks = tasks.filter(task_type=data["task_type"])
        if data.get("status"):
            tasks = tasks.filter(status=data["status"])
        if data.get("date_from"):
            tasks = tasks.filter(created_at__gte=data["date_from"])
        if data.get("date_to"):
            tasks = tasks.filter(created_at__lte=data["date_to"])
        if data.get("q"):
            q = data["q"].strip()
            if q:
                tasks = tasks.filter(room__room_number__icontains=q)

        prefix = "-" if data["sort_dir"] == "desc" else ""
        ordered = tasks.order_by(f"{prefix}{data['sort_by']}")
        total = ordered.count()
        offset = (data["page"] - 1) * data["page_size"]
        rows = ordered[offset:offset + data["page_size"]]
        return Response(
            {
                "count": total,
                "page": data["page"],
                "page_size": data["page_size"],
                "results": [_task_to_dict(task) for task in rows],
            },
            status=status.HTTP_200_OK,
        )


class HousekeepingTaskDetailView(APIView):
    def get(self, request, task_id: int):
        if not _has_permission(request.user, "housekeeping.view"):
            return Response({"detail": "Permission required: housekeeping.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        task = HousekeepingTask.objects.select_related("room", "room__property").filter(id=task_id, room__property__org_id=org_id).first()
        if not task:
            return Response({"detail": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"data": _task_to_dict(task)}, status=status.HTTP_200_OK)


class HousekeepingTaskTransitionView(APIView):
    target_status: str = ""
    action_name: str = ""

    def _validate_transition(self, task: HousekeepingTask) -> str | None:
        if self.action_name == "start":
            if task.status not in {HousekeepingTask.STATUS_ASSIGNED, HousekeepingTask.STATUS_PENDING}:
                return "Task can be started only from PENDING or ASSIGNED"
        elif self.action_name == "complete":
            if task.status != HousekeepingTask.STATUS_IN_PROGRESS:
                return "Task can be completed only from IN_PROGRESS"
        elif self.action_name == "verify":
            if task.status != HousekeepingTask.STATUS_COMPLETED:
                return "Task can be verified only from COMPLETED"
        elif self.action_name == "cancel":
            if task.status not in {HousekeepingTask.STATUS_PENDING, HousekeepingTask.STATUS_ASSIGNED, HousekeepingTask.STATUS_IN_PROGRESS}:
                return "Task can be cancelled only from active statuses"
        elif self.action_name == "reopen":
            if task.status not in {HousekeepingTask.STATUS_COMPLETED, HousekeepingTask.STATUS_CANCELLED}:
                return "Task can be reopened only from COMPLETED or CANCELLED"
        return None

    def post(self, request, task_id: int):
        if not _has_permission(request.user, "housekeeping.manage"):
            return Response({"detail": "Permission required: housekeeping.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = HousekeepingTaskActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        task = HousekeepingTask.objects.select_related("room", "room__property").filter(id=task_id, room__property__org_id=data["org_id"]).first()
        if not task:
            return Response({"detail": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        transition_error = self._validate_transition(task)
        if transition_error:
            return Response({"detail": transition_error}, status=status.HTTP_400_BAD_REQUEST)

        before = task.status
        note = data.get("note", "").strip()
        reason = data.get("reason", "").strip()
        if self.action_name == "verify":
            # Current schema has no VERIFIED status; keep COMPLETED and record verification in notes/audit.
            task.notes = f"{task.notes}\n[verified] {note}".strip() if note else task.notes
        elif self.action_name == "reopen":
            task.status = HousekeepingTask.STATUS_ASSIGNED if task.assigned_to_id else HousekeepingTask.STATUS_PENDING
        else:
            task.status = self.target_status
            if note:
                task.notes = f"{task.notes}\n[{self.action_name}] {note}".strip()
        task.save(update_fields=["status", "notes", "updated_at"])

        action = {
            "start": "housekeeping_task_started",
            "complete": "housekeeping_task_completed",
            "verify": "housekeeping_task_verified",
            "cancel": "housekeeping_task_cancelled",
            "reopen": "housekeeping_task_reopened",
        }.get(self.action_name, f"housekeeping_task_{self.action_name}")
        _audit(
            request,
            org_id=task.room.property.org_id,
            property_id=task.room.property_id,
            action=action,
            entity_type="housekeeping_task",
            entity_id=str(task.id),
            metadata={"before_status": before, "after_status": task.status, "note": note, "reason": reason},
            actor=request.user,
        )
        return Response({"data": _task_to_dict(task)}, status=status.HTTP_200_OK)


class HousekeepingTaskStartView(HousekeepingTaskTransitionView):
    target_status = HousekeepingTask.STATUS_IN_PROGRESS
    action_name = "start"


class HousekeepingTaskCompleteView(HousekeepingTaskTransitionView):
    target_status = HousekeepingTask.STATUS_COMPLETED
    action_name = "complete"


class HousekeepingTaskVerifyView(HousekeepingTaskTransitionView):
    action_name = "verify"


class HousekeepingTaskCancelView(HousekeepingTaskTransitionView):
    target_status = HousekeepingTask.STATUS_CANCELLED
    action_name = "cancel"


class HousekeepingTaskReopenView(HousekeepingTaskTransitionView):
    action_name = "reopen"


class RoomStatusUpsertView(APIView):
    service = HousekeepingService()

    def post(self, request):
        if not _has_permission(request.user, "housekeeping.manage"):
            return Response({"detail": "Permission required: housekeeping.manage"}, status=status.HTTP_403_FORBIDDEN)

        serializer = RoomStatusUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        room = Room.objects.filter(id=data["room_id"]).first()
        if not room:
            return Response({"detail": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            room_status = self.service.upsert_room_status(
                room=room,
                occupancy_status=data["occupancy_status"],
                housekeeping_status=data["housekeeping_status"],
                priority=data.get("priority", RoomStatus.PRIORITY_MEDIUM),
                updated_by=request.user,
                reason=data.get("reason", ""),
            )
        except HousekeepingValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        _audit(
            request,
            org_id=room.property.org_id,
            property_id=room.property_id,
            action="room_status_changed",
            entity_type="room_status",
            entity_id=str(room_status.id),
            metadata=_room_status_to_dict(room_status),
            actor=request.user,
        )
        return Response({"data": _room_status_to_dict(room_status)}, status=status.HTTP_200_OK)


class HousekeepingTaskGenerateView(APIView):
    service = TaskGenerationService()

    def post(self, request):
        if not _has_permission(request.user, "housekeeping.manage"):
            return Response({"detail": "Permission required: housekeeping.manage"}, status=status.HTTP_403_FORBIDDEN)

        property_id = int(request.data.get("property_id", 0))
        if not property_id:
            return Response({"detail": "property_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        statuses = RoomStatus.objects.select_related("room", "room__property").filter(room__property_id=property_id)
        created = self.service.generate_batch(room_statuses=statuses)
        prop = statuses.first().room.property if statuses.exists() else None
        if prop:
            _audit(
                request,
                org_id=prop.org_id,
                property_id=prop.id,
                action="housekeeping_task_generated",
                entity_type="housekeeping_task",
                entity_id="batch",
                metadata={"created_tasks": created},
                actor=request.user,
            )
        return Response({"data": {"created_tasks": created}}, status=status.HTTP_200_OK)


class HousekeepingTaskAssignView(APIView):
    service = TaskAssignmentService()

    def post(self, request):
        if not _has_permission(request.user, "housekeeping.manage"):
            return Response({"detail": "Permission required: housekeeping.manage"}, status=status.HTTP_403_FORBIDDEN)

        serializer = HousekeepingAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        strategy = data["strategy"]

        if strategy == "round_robin":
            assigned = self.service.assign_round_robin(org_id=data["org_id"], property_id=data["property_id"], changed_by=request.user)
        elif strategy == "priority_first":
            assigned = self.service.assign_least_loaded(org_id=data["org_id"], property_id=data["property_id"], changed_by=request.user)
        else:
            assigned = self.service.assign_least_loaded(org_id=data["org_id"], property_id=data["property_id"], changed_by=request.user)

        _audit(
            request,
            org_id=data["org_id"],
            property_id=data["property_id"],
            action="housekeeping_task_assigned",
            entity_type="housekeeping_task",
            entity_id="batch",
            metadata={"assigned_tasks": assigned, "strategy": strategy},
            actor=request.user,
        )
        return Response({"data": {"assigned_tasks": assigned}}, status=status.HTTP_200_OK)


class HousekeepingTaskReassignOverdueView(APIView):
    service = TaskAssignmentService()

    def post(self, request):
        if not _has_permission(request.user, "housekeeping.manage"):
            return Response({"detail": "Permission required: housekeeping.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        property_id = int(request.data.get("property_id", 0))
        if not org_id or not property_id:
            return Response({"detail": "org_id and property_id are required"}, status=status.HTTP_400_BAD_REQUEST)
        count = self.service.reassign_overdue(org_id=org_id, property_id=property_id, changed_by=request.user)
        return Response({"data": {"reassigned": count}}, status=status.HTTP_200_OK)


class HousekeepingKPISummaryView(APIView):
    service = KPIService()

    def get(self, request):
        if not _has_permission(request.user, "housekeeping.view"):
            return Response({"detail": "Permission required: housekeeping.view"}, status=status.HTTP_403_FORBIDDEN)

        serializer = HousekeepingKPIFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = self.service.summary(**data)
        _audit(request, org_id=data["org_id"], property_id=data.get("property_id"), action="housekeeping_kpi_viewed", entity_type="housekeeping_kpi", entity_id="summary", metadata=data, actor=request.user)
        return Response({"data": result})


class HousekeepingKPIStaffPerformanceView(APIView):
    service = KPIService()

    def get(self, request):
        if not _has_permission(request.user, "housekeeping.view"):
            return Response({"detail": "Permission required: housekeeping.view"}, status=status.HTTP_403_FORBIDDEN)

        serializer = HousekeepingKPIFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = self.service.staff_performance(**data)
        return Response({"data": {"results": result}})


class HousekeepingKPIRoomTurnaroundView(APIView):
    service = KPIService()

    def get(self, request):
        if not _has_permission(request.user, "housekeeping.view"):
            return Response({"detail": "Permission required: housekeeping.view"}, status=status.HTTP_403_FORBIDDEN)

        serializer = HousekeepingKPIFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = self.service.room_turnaround(**data)
        return Response({"data": result})


class PMSAuthMixin:
    def _idempotency_key(self, request) -> str:
        return request.headers.get("Idempotency-Key", "") or request.headers.get("X-Idempotency-Key", "")


class PMSRoomStatusSyncView(PMSAuthMixin, APIView):
    service = PMSSyncService()

    def post(self, request):
        serializer = PMSRoomStatusSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        room = Room.objects.filter(id=data["room_id"]).first()
        if not room:
            return Response({"detail": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            status_row = self.service.sync_room_status(
                room=room,
                external_reference_id=data["external_reference_id"],
                occupancy_status=data["occupancy_status"],
                housekeeping_status=data["housekeeping_status"],
                timestamp=data["timestamp"],
                updated_by=None,
                idempotency_key=self._idempotency_key(request),
            )
            _audit(request, org_id=room.property.org_id, property_id=room.property_id, action="pms_sync_received", entity_type="pms_room_status", entity_id=data["external_reference_id"], metadata=data, actor=None)
        except Exception as exc:
            PMSSyncLog.objects.create(source="pms_room_status", event_key=data["external_reference_id"], payload_json=data, external_reference_id=data["external_reference_id"], status="FAILED", error_message=str(exc))
            _audit(request, org_id=room.property.org_id, property_id=room.property_id, action="pms_sync_failed", entity_type="pms_room_status", entity_id=data["external_reference_id"], metadata={"error": str(exc), **data}, actor=None)
            return Response({"success": False, "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"success": True, "data": _room_status_to_dict(status_row)}, status=status.HTTP_200_OK)


class PMSRoomStatusPullView(PMSAuthMixin, APIView):
    service = PMSSyncService()

    def get(self, request):
        serializer = PMSRoomStatusPullSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        rows = self.service.pull_room_status(property_id=serializer.validated_data.get("property_id"))
        return Response({"success": True, "data": {"results": [_room_status_to_dict(row) for row in rows]}})


class PMSTaskSyncView(PMSAuthMixin, APIView):
    service = PMSSyncService()

    def post(self, request):
        serializer = HousekeepingTaskSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        task = HousekeepingTask.objects.filter(id=data["task_id"]).first()
        if not task:
            return Response({"detail": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            updated = self.service.sync_task_update(
                task=task,
                status_value=data["status"],
                timestamp=data["timestamp"],
                external_reference_id=data.get("external_reference_id", ""),
                idempotency_key=self._idempotency_key(request),
            )
            _audit(request, org_id=task.room.property.org_id, property_id=task.room.property_id, action="pms_sync_received", entity_type="pms_housekeeping_task", entity_id=str(task.id), metadata=data, actor=None)
            return Response({"success": True, "data": {"task_id": updated.id, "status": updated.status}}, status=status.HTTP_200_OK)
        except Exception as exc:
            _audit(request, org_id=task.room.property.org_id, property_id=task.room.property_id, action="pms_sync_failed", entity_type="pms_housekeeping_task", entity_id=str(task.id), metadata={"error": str(exc), **data}, actor=None)
            return Response({"success": False, "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
