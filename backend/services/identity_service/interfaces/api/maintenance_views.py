from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.services.audit_logging import AuditContext
from application.services.maintenance import (
    AssetFilters,
    AssetService,
    MaintenanceLogbookService,
    MaintenanceNotFoundError,
    MaintenanceService,
    MaintenanceTaskFilters,
    MaintenanceTransitionError,
    MaintenanceValidationError,
    PMScheduleRepository,
    PMSchedulerService,
    QRAssetService,
)
from infrastructure.db.core.models import Asset, MaintenanceTask, PMSchedule, RolePermission, User, UserRole
from infrastructure.services.audit_logging import get_audit_logger
from interfaces.api.serializers import (
    AssetCreateSerializer,
    AssetStatusUpdateSerializer,
    AssetUpdateSerializer,
    MaintenanceTaskAssignSerializer,
    MaintenanceTaskCreateSerializer,
    MaintenanceTaskCostsPatchSerializer,
    MaintenanceTaskLogbookCreateSerializer,
    MaintenanceTaskTransitionSerializer,
    MaintenanceTaskUpdateSerializer,
    PMScheduleCreateSerializer,
    PMScheduleUpdateSerializer,
    QRTaskCreateSerializer,
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
    meta = getattr(request, "audit_context", {})
    return AuditContext(
        org_id=org_id,
        property_id=property_id,
        actor_user_id=getattr(actor, "id", None),
        ip_address=meta.get("ip_address", request.META.get("REMOTE_ADDR", "")),
        user_agent=meta.get("user_agent", request.META.get("HTTP_USER_AGENT", "")),
    )


def _audit(request, *, org_id: int, action: str, entity_type: str, entity_id: str, metadata=None, property_id=None, actor=None):
    try:
        get_audit_logger().log_action(
            action=action,
            target_type=entity_type,
            target_id=str(entity_id),
            metadata=metadata or {},
            context=_audit_context(request, org_id=org_id, property_id=property_id, actor=actor),
        )
    except Exception:
        pass


def _asset_dict(asset: Asset) -> dict:
    return {
        "id": asset.id,
        "org_id": asset.org_id,
        "asset_code": asset.asset_code,
        "qr_code": asset.qr_code,
        "name": asset.name,
        "description": asset.description,
        "category": asset.category,
        "location_id": asset.location_id,
        "room_id": asset.room_id,
        "department_id": asset.department_id,
        "property_id": asset.property_id,
        "manufacturer": asset.manufacturer,
        "model_number": asset.model_number,
        "serial_number": asset.serial_number,
        "purchase_date": asset.purchase_date,
        "warranty_expiry_date": asset.warranty_expiry_date,
        "status": asset.status,
        "criticality": asset.criticality,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
        "created_by": asset.created_by_id,
        "updated_by": asset.updated_by_id,
    }


def _task_dict(task: MaintenanceTask) -> dict:
    return {
        "id": task.id,
        "org_id": task.org_id,
        "task_number": task.task_number,
        "task_type": task.task_type,
        "title": task.title,
        "description": task.description,
        "asset_id": task.asset_id,
        "room_id": task.room_id,
        "property_id": task.property_id,
        "department_id": task.department_id,
        "priority": task.priority,
        "status": task.status,
        "assigned_to": task.assigned_to_id,
        "reported_by": task.reported_by_id,
        "scheduled_at": task.scheduled_at,
        "due_at": task.due_at,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "parts_total": task.parts_total,
        "labor_total": task.labor_total,
        "total_cost": task.total_cost,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


class AssetListCreateView(APIView):
    service = AssetService()

    def post(self, request):
        if not _has_permission(request.user, "maintenance.assets.manage"):
            return Response({"detail": "Permission required: maintenance.assets.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = AssetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        asset = self.service.create_asset(created_by=request.user, org_id=data["org_id"], **{k: v for k, v in data.items() if k != "org_id"})
        _audit(request, org_id=asset.org_id, action="asset_created", entity_type="asset", entity_id=str(asset.id), metadata={"asset_code": asset.asset_code}, property_id=asset.property_id, actor=request.user)
        return Response(_asset_dict(asset), status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "maintenance.assets.view"):
            return Response({"detail": "Permission required: maintenance.assets.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        filters = AssetFilters(
            org_id=org_id,
            status=request.query_params.get("status"),
            category=request.query_params.get("category"),
            location_id=int(request.query_params["location"]) if request.query_params.get("location") else None,
            room_id=int(request.query_params["room"]) if request.query_params.get("room") else None,
            department_id=int(request.query_params["department"]) if request.query_params.get("department") else None,
            property_id=int(request.query_params["property"]) if request.query_params.get("property") else None,
            criticality=request.query_params.get("criticality"),
            warranty_expiring_before=request.query_params.get("warranty_expiring_before") or None,
        )
        if isinstance(filters.warranty_expiring_before, str):
            from django.utils.dateparse import parse_date
            filters.warranty_expiring_before = parse_date(filters.warranty_expiring_before)
        qs = self.service.list_assets(filters=filters)
        q = request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(asset_code__icontains=q) | Q(serial_number__icontains=q))
        page = max(int(request.query_params.get("page", "1") or "1"), 1)
        page_size = min(max(int(request.query_params.get("page_size", "10") or "10"), 1), 100)
        total = qs.count()
        offset = (page - 1) * page_size
        rows = qs.order_by("-created_at")[offset:offset + page_size]
        return Response({"count": total, "page": page, "page_size": page_size, "results": [_asset_dict(row) for row in rows]})


class AssetDetailView(APIView):
    service = AssetService()

    def get(self, request, asset_id: int):
        if not _has_permission(request.user, "maintenance.assets.view"):
            return Response({"detail": "Permission required: maintenance.assets.view"}, status=status.HTTP_403_FORBIDDEN)
        try:
            asset = self.service.get_asset(asset_id=asset_id, org_id=int(request.query_params.get("org_id", "0")))
        except MaintenanceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(_asset_dict(asset), status=status.HTTP_200_OK)

    def patch(self, request, asset_id: int):
        if not _has_permission(request.user, "maintenance.assets.manage"):
            return Response({"detail": "Permission required: maintenance.assets.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = AssetUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        try:
            asset = self.service.get_asset(asset_id=asset_id, org_id=org_id)
        except MaintenanceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        updated = self.service.update_asset(asset=asset, updated_by=request.user, **serializer.validated_data)
        _audit(request, org_id=updated.org_id, action="asset_updated", entity_type="asset", entity_id=str(updated.id), metadata={"name": updated.name}, property_id=updated.property_id, actor=request.user)
        return Response(_asset_dict(updated), status=status.HTTP_200_OK)


class AssetStatusUpdateView(APIView):
    service = AssetService()

    def post(self, request, asset_id: int):
        if not _has_permission(request.user, "maintenance.assets.manage"):
            return Response({"detail": "Permission required: maintenance.assets.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = AssetStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            asset = self.service.get_asset(asset_id=asset_id, org_id=data["org_id"])
            updated = self.service.change_status(asset=asset, new_status=data["new_status"], changed_by=request.user, reason=data.get("reason", ""), metadata=data.get("metadata", {}))
        except MaintenanceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except MaintenanceTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=updated.org_id, action="asset_status_changed", entity_type="asset", entity_id=str(updated.id), metadata={"new_status": updated.status, "reason": data.get("reason", "")}, property_id=updated.property_id, actor=request.user)
        return Response(_asset_dict(updated), status=status.HTTP_200_OK)


class AssetHistoryView(APIView):
    service = AssetService()

    def get(self, request, asset_id: int):
        if not _has_permission(request.user, "maintenance.assets.view"):
            return Response({"detail": "Permission required: maintenance.assets.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            asset = self.service.get_asset(asset_id=asset_id, org_id=org_id)
        except MaintenanceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        rows = self.service.history_repository.list_for_asset(asset_id=asset.id)
        return Response(
            {
                "count": rows.count(),
                "results": [
                    {
                        "id": row.id,
                        "asset_id": row.asset_id,
                        "previous_status": row.previous_status,
                        "new_status": row.new_status,
                        "changed_by": row.changed_by_id,
                        "changed_at": row.changed_at,
                        "reason": row.reason,
                        "metadata": row.metadata_json,
                    }
                    for row in rows
                ],
            }
        )


class MaintenanceTaskListCreateView(APIView):
    service = MaintenanceService()

    def post(self, request):
        if not _has_permission(request.user, "maintenance.tasks.manage"):
            return Response({"detail": "Permission required: maintenance.tasks.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = MaintenanceTaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        assignee = None
        if data.get("assigned_to"):
            assignee = User.objects.filter(id=data["assigned_to"], org_id=data["org_id"]).first()
            if not assignee:
                return Response({"detail": "Assignee not found in organization"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            task = self.service.create_task(reported_by=request.user, org_id=data["org_id"], assigned_to=assignee, **{k: v for k, v in data.items() if k not in {"org_id", "assigned_to"}})
        except MaintenanceValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=task.org_id, action="maintenance_task_created", entity_type="maintenance_task", entity_id=str(task.id), metadata={"task_number": task.task_number, "task_type": task.task_type}, property_id=task.property_id, actor=request.user)
        return Response(_task_dict(task), status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "maintenance.tasks.view"):
            return Response({"detail": "Permission required: maintenance.tasks.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        filters = MaintenanceTaskFilters(
            org_id=org_id,
            task_type=request.query_params.get("task_type"),
            status=request.query_params.get("status"),
            priority=request.query_params.get("priority"),
            asset_id=int(request.query_params["asset"]) if request.query_params.get("asset") else None,
            room_id=int(request.query_params["room"]) if request.query_params.get("room") else None,
            property_id=int(request.query_params["property"]) if request.query_params.get("property") else None,
            department_id=int(request.query_params["department"]) if request.query_params.get("department") else None,
            assigned_to=int(request.query_params["assigned_to"]) if request.query_params.get("assigned_to") else None,
        )
        qs = self.service.list_tasks(filters=filters)
        if request.query_params.get("date_from"):
            from django.utils.dateparse import parse_datetime
            parsed = parse_datetime(request.query_params["date_from"])
            if parsed:
                qs = qs.filter(created_at__gte=parsed)
        if request.query_params.get("date_to"):
            from django.utils.dateparse import parse_datetime
            parsed = parse_datetime(request.query_params["date_to"])
            if parsed:
                qs = qs.filter(created_at__lte=parsed)
        page = max(int(request.query_params.get("page", "1") or "1"), 1)
        page_size = min(max(int(request.query_params.get("page_size", "10") or "10"), 1), 100)
        total = qs.count()
        offset = (page - 1) * page_size
        rows = qs.order_by("-created_at")[offset:offset + page_size]
        return Response({"count": total, "page": page, "page_size": page_size, "results": [_task_dict(row) for row in rows]})


class MaintenanceTaskDetailView(APIView):
    service = MaintenanceService()

    def get(self, request, task_id: int):
        if not _has_permission(request.user, "maintenance.tasks.view"):
            return Response({"detail": "Permission required: maintenance.tasks.view"}, status=status.HTTP_403_FORBIDDEN)
        try:
            task = self.service.get_task(task_id=task_id, org_id=int(request.query_params.get("org_id", "0")))
        except MaintenanceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(_task_dict(task), status=status.HTTP_200_OK)

    def patch(self, request, task_id: int):
        if not _has_permission(request.user, "maintenance.tasks.manage"):
            return Response({"detail": "Permission required: maintenance.tasks.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = MaintenanceTaskUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            task = self.service.get_task(task_id=task_id, org_id=int(request.data.get("org_id", 0)))
            task = self.service.update_task(task=task, **serializer.validated_data)
        except MaintenanceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except MaintenanceValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(_task_dict(task), status=status.HTTP_200_OK)


class MaintenanceTaskAssignView(APIView):
    service = MaintenanceService()

    def post(self, request, task_id: int):
        if not _has_permission(request.user, "maintenance.tasks.manage"):
            return Response({"detail": "Permission required: maintenance.tasks.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = MaintenanceTaskAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            task = self.service.get_task(task_id=task_id, org_id=data["org_id"])
        except MaintenanceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        assignee = User.objects.filter(id=data["assignee_id"], org_id=data["org_id"]).first()
        if not assignee:
            return Response({"detail": "Assignee not found in organization"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            task = self.service.assign(task=task, assignee=assignee)
        except MaintenanceTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=task.org_id, action="maintenance_task_assigned", entity_type="maintenance_task", entity_id=str(task.id), metadata={"assignee_id": assignee.id}, property_id=task.property_id, actor=request.user)
        return Response(_task_dict(task), status=status.HTTP_200_OK)


class MaintenanceTaskTransitionView(APIView):
    service = MaintenanceService()
    transition_status = ""
    action_name = ""

    def post(self, request, task_id: int):
        if not _has_permission(request.user, "maintenance.tasks.manage"):
            return Response({"detail": "Permission required: maintenance.tasks.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = MaintenanceTaskTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            task = self.service.get_task(task_id=task_id, org_id=data["org_id"])
            if self.action_name == "complete":
                if not MaintenanceLogbookService().has_completion_summary(task=task):
                    return Response({"detail": "Completion summary is required before completing task"}, status=status.HTTP_400_BAD_REQUEST)
            task = self.service.transition(task=task, to_status=self.transition_status)
        except MaintenanceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except MaintenanceTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=task.org_id, action=f"maintenance_task_{self.action_name}", entity_type="maintenance_task", entity_id=str(task.id), metadata={"status": task.status}, property_id=task.property_id, actor=request.user)
        return Response(_task_dict(task), status=status.HTTP_200_OK)


class MaintenanceTaskStartView(MaintenanceTaskTransitionView):
    transition_status = MaintenanceTask.STATUS_IN_PROGRESS
    action_name = "started"


class MaintenanceTaskHoldView(MaintenanceTaskTransitionView):
    transition_status = MaintenanceTask.STATUS_ON_HOLD
    action_name = "hold"


class MaintenanceTaskCompleteView(MaintenanceTaskTransitionView):
    transition_status = MaintenanceTask.STATUS_COMPLETED
    action_name = "completed"


class MaintenanceTaskCancelView(MaintenanceTaskTransitionView):
    transition_status = MaintenanceTask.STATUS_CANCELLED
    action_name = "cancelled"


class MaintenanceTaskVoidView(MaintenanceTaskTransitionView):
    transition_status = MaintenanceTask.STATUS_VOID
    action_name = "void"


class MaintenanceTaskLogbookView(APIView):
    task_service = MaintenanceService()
    logbook_service = MaintenanceLogbookService()

    def post(self, request, task_id: int):
        if not _has_permission(request.user, "maintenance.tasks.manage"):
            return Response({"detail": "Permission required: maintenance.tasks.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = MaintenanceTaskLogbookCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            task = self.task_service.get_task(task_id=task_id, org_id=data["org_id"])
            entry = self.logbook_service.add_entry(task=task, actor=request.user, entry_type=data["entry_type"], description=data["description"], parts=data.get("parts", []), labor=data.get("labor", []))
        except MaintenanceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except MaintenanceValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=task.org_id, action="logbook_entry_added", entity_type="maintenance_task", entity_id=str(task.id), metadata={"entry_id": entry.id, "entry_type": entry.entry_type}, property_id=task.property_id, actor=request.user)
        if data.get("parts"):
            _audit(request, org_id=task.org_id, action="parts_cost_added", entity_type="maintenance_task", entity_id=str(task.id), metadata={"entry_id": entry.id, "parts_count": len(data.get("parts", []))}, property_id=task.property_id, actor=request.user)
        if data.get("labor"):
            _audit(request, org_id=task.org_id, action="labor_cost_added", entity_type="maintenance_task", entity_id=str(task.id), metadata={"entry_id": entry.id, "labor_count": len(data.get("labor", []))}, property_id=task.property_id, actor=request.user)
        return Response({"id": entry.id, "maintenance_task_id": entry.maintenance_task_id, "entry_type": entry.entry_type, "description": entry.description, "created_by": entry.created_by_id, "created_at": entry.created_at}, status=status.HTTP_201_CREATED)

    def get(self, request, task_id: int):
        if not _has_permission(request.user, "maintenance.tasks.view"):
            return Response({"detail": "Permission required: maintenance.tasks.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            self.task_service.get_task(task_id=task_id, org_id=org_id)
        except MaintenanceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        rows = self.logbook_service.list_entries(task_id=task_id)
        return Response(
            {
                "count": rows.count(),
                "results": [
                    {
                        "id": row.id,
                        "maintenance_task_id": row.maintenance_task_id,
                        "asset_id": row.asset_id,
                        "entry_type": row.entry_type,
                        "description": row.description,
                        "created_by": row.created_by_id,
                        "created_at": row.created_at,
                        "parts": [
                            {
                                "id": p.id,
                                "part_name": p.part_name,
                                "part_number": p.part_number,
                                "quantity": p.quantity,
                                "unit_cost": p.unit_cost,
                                "total_cost": p.total_cost,
                            }
                            for p in row.parts_entries.all()
                        ],
                        "labor": [
                            {
                                "id": l.id,
                                "technician_id": l.technician_id,
                                "hours": l.hours,
                                "hourly_rate": l.hourly_rate,
                                "total_labor_cost": l.total_labor_cost,
                            }
                            for l in row.labor_entries.all()
                        ],
                    }
                    for row in rows
                ],
            }
        )


class MaintenanceTaskCostsView(APIView):
    task_service = MaintenanceService()
    logbook_service = MaintenanceLogbookService()

    def patch(self, request, task_id: int):
        if not _has_permission(request.user, "maintenance.tasks.manage"):
            return Response({"detail": "Permission required: maintenance.tasks.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = MaintenanceTaskCostsPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            task = self.task_service.get_task(task_id=task_id, org_id=serializer.validated_data["org_id"])
            task = self.logbook_service.update_task_costs(task=task)
        except MaintenanceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(_task_dict(task), status=status.HTTP_200_OK)


class PMScheduleListCreateView(APIView):
    repo = PMScheduleRepository()

    def post(self, request):
        if not _has_permission(request.user, "maintenance.pm.manage"):
            return Response({"detail": "Permission required: maintenance.pm.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = PMScheduleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        asset = Asset.objects.filter(id=data["asset_id"], org_id=data["org_id"]).first()
        if not asset:
            return Response({"detail": "Asset not found"}, status=status.HTTP_404_NOT_FOUND)
        schedule = self.repo.create(asset=asset, created_by=request.user, **{k: v for k, v in data.items() if k not in {"org_id", "asset_id"}})
        _audit(request, org_id=data["org_id"], action="pm_schedule_created", entity_type="pm_schedule", entity_id=str(schedule.id), metadata={"asset_id": schedule.asset_id}, property_id=asset.property_id, actor=request.user)
        return Response({"id": schedule.id}, status=status.HTTP_201_CREATED)


class PMScheduleDetailView(APIView):
    repo = PMScheduleRepository()

    def patch(self, request, schedule_id: int):
        if not _has_permission(request.user, "maintenance.pm.manage"):
            return Response({"detail": "Permission required: maintenance.pm.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = PMScheduleUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        schedule = PMSchedule.objects.select_related("asset").filter(id=schedule_id, asset__org_id=org_id).first()
        if not schedule:
            return Response({"detail": "Schedule not found"}, status=status.HTTP_404_NOT_FOUND)
        for k, v in serializer.validated_data.items():
            setattr(schedule, k, v)
        self.repo.save(schedule)
        _audit(request, org_id=org_id, action="pm_schedule_updated", entity_type="pm_schedule", entity_id=str(schedule.id), metadata={"is_active": schedule.is_active}, property_id=schedule.asset.property_id, actor=request.user)
        return Response({"id": schedule.id}, status=status.HTTP_200_OK)


class PMSchedulerRunView(APIView):
    service = PMSchedulerService()

    def post(self, request):
        if not _has_permission(request.user, "maintenance.pm.manage"):
            return Response({"detail": "Permission required: maintenance.pm.manage"}, status=status.HTTP_403_FORBIDDEN)
        summary = self.service.run(actor=request.user)
        _audit(request, org_id=int(request.data.get("org_id", 0) or 0), action="pm_task_generated", entity_type="pm_scheduler", entity_id="run", metadata=summary, actor=request.user)
        return Response(summary, status=status.HTTP_200_OK)


class QRAssetLookupView(APIView):
    service = QRAssetService()

    def get(self, request, qr_code: str):
        if not _has_permission(request.user, "maintenance.assets.view"):
            return Response({"detail": "Permission required: maintenance.assets.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            context = self.service.lookup_with_context(org_id=org_id, qr_code=qr_code)
        except MaintenanceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        asset = context["asset"]
        _audit(request, org_id=org_id, action="asset_qr_lookup", entity_type="asset", entity_id=str(asset.id), metadata={"qr_code": qr_code}, property_id=asset.property_id, actor=request.user)
        return Response(
            {
                "asset": _asset_dict(asset),
                "current_status": asset.status,
                "open_maintenance_tasks": [_task_dict(t) for t in context["open_tasks"]],
                "recent_logbook_entries": [
                    {
                        "id": e.id,
                        "entry_type": e.entry_type,
                        "description": e.description,
                        "created_at": e.created_at,
                    }
                    for e in context["recent_entries"]
                ],
            },
            status=status.HTTP_200_OK,
        )


class QRTaskCreateView(APIView):
    service = QRAssetService()

    def post(self, request, qr_code: str):
        if not _has_permission(request.user, "maintenance.tasks.manage"):
            return Response({"detail": "Permission required: maintenance.tasks.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = QRTaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            task = self.service.create_task_from_qr(org_id=data["org_id"], qr_code=qr_code, reported_by=request.user, **{k: v for k, v in data.items() if k not in {"org_id", "task_type"}})
        except MaintenanceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        _audit(request, org_id=task.org_id, action="maintenance_task_created", entity_type="maintenance_task", entity_id=str(task.id), metadata={"source": "qr", "qr_code": qr_code}, property_id=task.property_id, actor=request.user)
        return Response(_task_dict(task), status=status.HTTP_201_CREATED)
