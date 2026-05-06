from datetime import datetime
from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.services.audit_logging import AuditContext
from infrastructure.db.core.models import (
    AuditLog,
    FoodBeverageBreakfastCount,
    FoodBeverageOutletReadiness,
    FoodBeverageTask,
    Property,
    RolePermission,
    User,
    UserRole,
)
from infrastructure.services.audit_logging import get_audit_logger
from interfaces.api.serializers import (
    FBBreakfastCountCreateSerializer,
    FBBreakfastCountUpdateSerializer,
    FBOutletReadinessActionSerializer,
    FBOutletReadinessCreateSerializer,
    FBOutletReadinessUpdateSerializer,
    FBTaskActionSerializer,
    FBTaskAssignSerializer,
    FBTaskCreateSerializer,
    FBTaskUpdateSerializer,
)


def _has_permission(user, code: str) -> bool:
    if not user:
        return False
    if hasattr(user, "is_authenticated") and not user.is_authenticated:
        return False
    if UserRole.objects.filter(user=user, role__name__iexact="super admin").exists():
        return True
    return RolePermission.objects.filter(role__user_roles__user=user, permission__code=code).exists()


def _audit(request, *, org_id: int, action: str, target_type: str, target_id: str, metadata=None, property_id=None):
    meta = getattr(request, "audit_context", {})
    try:
        get_audit_logger().log_action(
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            metadata=metadata or {},
            context=AuditContext(
                org_id=org_id,
                property_id=property_id,
                actor_user_id=getattr(request.user, "id", None),
                ip_address=meta.get("ip_address", request.META.get("REMOTE_ADDR", "")),
                user_agent=meta.get("user_agent", request.META.get("HTTP_USER_AGENT", "")),
            ),
        )
    except Exception:
        pass


def _paginate(qs, request):
    page = max(int(request.query_params.get("page", "1") or "1"), 1)
    page_size = min(max(int(request.query_params.get("page_size", "10") or "10"), 1), 100)
    total = qs.count()
    offset = (page - 1) * page_size
    return total, page, page_size, qs[offset: offset + page_size]


def _breakfast_dict(row):
    return {
        "id": row.id,
        "service_date": row.service_date,
        "property_id": row.property_id,
        "outlet_id": row.outlet_id,
        "expected_guest_count": row.expected_guest_count,
        "actual_guest_count": row.actual_guest_count,
        "in_house_guest_count": row.in_house_guest_count,
        "complimentary_count": row.complimentary_count,
        "paid_count": row.paid_count,
        "no_show_count": row.no_show_count,
        "notes": row.notes,
        "recorded_by": row.recorded_by_id,
        "updated_at": row.updated_at,
    }


def _readiness_dict(row):
    return {
        "id": row.id,
        "readiness_date": row.readiness_date,
        "property_id": row.property_id,
        "outlet_id": row.outlet_id,
        "shift": row.shift,
        "status": row.status,
        "checklist_score": float(row.checklist_score),
        "verified_by": row.verified_by_id,
        "verified_at": row.verified_at,
        "updated_at": row.updated_at,
        "checklist_items": row.checklist_items,
    }


def _task_dict(row):
    return {
        "id": row.id,
        "task_number": row.task_number,
        "property_id": row.property_id,
        "outlet_id": row.outlet_id,
        "title": row.title,
        "task_type": row.task_type,
        "priority": row.priority,
        "status": row.status,
        "assigned_to": row.assigned_to_id,
        "due_at": row.due_at,
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "updated_at": row.updated_at,
    }


class FBBreakfastCountListCreateView(APIView):
    def post(self, request):
        ser = FBBreakfastCountCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        prop = Property.objects.filter(id=data["property_id"], org_id=data["org_id"]).first()
        if not prop:
            return Response({"detail": "Property not found"}, status=status.HTTP_400_BAD_REQUEST)
        row = FoodBeverageBreakfastCount.objects.create(recorded_by=request.user, **data)
        _audit(request, org_id=row.org_id, action="breakfast_count_created", target_type="food_beverage_breakfast_count", target_id=str(row.id), property_id=row.property_id)
        return Response(_breakfast_dict(row), status=status.HTTP_201_CREATED)

    def get(self, request):
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        qs = FoodBeverageBreakfastCount.objects.filter(org_id=org_id)
        if request.query_params.get("property_id"):
            qs = qs.filter(property_id=int(request.query_params["property_id"]))
        if request.query_params.get("outlet_id"):
            qs = qs.filter(outlet_id=int(request.query_params["outlet_id"]))
        if request.query_params.get("date_from"):
            qs = qs.filter(service_date__gte=request.query_params["date_from"])
        if request.query_params.get("date_to"):
            qs = qs.filter(service_date__lte=request.query_params["date_to"])
        total, page, page_size, rows = _paginate(qs.order_by("-updated_at"), request)
        return Response({"count": total, "page": page, "page_size": page_size, "results": [_breakfast_dict(x) for x in rows]})


class FBBreakfastCountDetailView(APIView):
    def get(self, request, id: int):
        row = FoodBeverageBreakfastCount.objects.filter(id=id, org_id=int(request.query_params.get("org_id", "0"))).first()
        if not row:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_breakfast_dict(row))

    def patch(self, request, id: int):
        ser = FBBreakfastCountUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        row = FoodBeverageBreakfastCount.objects.filter(id=id, org_id=data["org_id"]).first()
        if not row:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        for k, v in data.items():
            if k != "org_id":
                setattr(row, k, v)
        row.save(update_fields=[k for k in data.keys() if k != "org_id"] + ["updated_at"])
        _audit(request, org_id=row.org_id, action="breakfast_count_updated", target_type="food_beverage_breakfast_count", target_id=str(row.id), property_id=row.property_id)
        return Response(_breakfast_dict(row))


class FBOutletReadinessListCreateView(APIView):
    def post(self, request):
        ser = FBOutletReadinessCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        row = FoodBeverageOutletReadiness.objects.create(**data)
        _audit(request, org_id=row.org_id, action="outlet_readiness_created", target_type="food_beverage_outlet_readiness", target_id=str(row.id), property_id=row.property_id)
        return Response(_readiness_dict(row), status=status.HTTP_201_CREATED)

    def get(self, request):
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        qs = FoodBeverageOutletReadiness.objects.filter(org_id=org_id)
        for f in ["property_id", "outlet_id", "shift", "status"]:
            if request.query_params.get(f):
                qs = qs.filter(**{f: request.query_params[f]})
        if request.query_params.get("date_from"):
            qs = qs.filter(readiness_date__gte=request.query_params["date_from"])
        if request.query_params.get("date_to"):
            qs = qs.filter(readiness_date__lte=request.query_params["date_to"])
        total, page, page_size, rows = _paginate(qs.order_by("-updated_at"), request)
        return Response({"count": total, "page": page, "page_size": page_size, "results": [_readiness_dict(x) for x in rows]})


class FBOutletReadinessDetailView(APIView):
    def get(self, request, id: int):
        row = FoodBeverageOutletReadiness.objects.filter(id=id, org_id=int(request.query_params.get("org_id", "0"))).first()
        if not row:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_readiness_dict(row))

    def patch(self, request, id: int):
        ser = FBOutletReadinessUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        row = FoodBeverageOutletReadiness.objects.filter(id=id, org_id=data["org_id"]).first()
        if not row:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        if data.get("checklist_item_id") and data.get("result"):
            updated = []
            for item in row.checklist_items or []:
                if item.get("id") == data["checklist_item_id"]:
                    item["result"] = data["result"]
                    item["comment"] = data.get("comment", item.get("comment", ""))
                    item["completed_by"] = getattr(request.user, "id", None)
                    item["completed_at"] = timezone.now().isoformat()
                updated.append(item)
            row.checklist_items = updated
        if "checklist_items" in data:
            row.checklist_items = data["checklist_items"]
        if "status" in data:
            row.status = data["status"]
        results = [x.get("result") for x in (row.checklist_items or []) if x.get("result")]
        pass_count = len([x for x in results if x == "PASS" or x == "N/A"])
        row.checklist_score = (pass_count / len(results) * 100) if results else 0
        row.save()
        _audit(request, org_id=row.org_id, action="outlet_readiness_updated", target_type="food_beverage_outlet_readiness", target_id=str(row.id), property_id=row.property_id)
        return Response(_readiness_dict(row))


class FBOutletReadinessActionView(APIView):
    action_name = ""

    def post(self, request, id: int):
        ser = FBOutletReadinessActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        row = FoodBeverageOutletReadiness.objects.filter(id=id, org_id=ser.validated_data["org_id"]).first()
        if not row:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        if self.action_name == "start":
            row.status = "IN_PROGRESS"
        elif self.action_name == "submit":
            row.status = "READY"
        elif self.action_name == "verify":
            row.status = "VERIFIED"
            row.verified_by = request.user
            row.verified_at = timezone.now()
        elif self.action_name == "void":
            row.status = "VOID"
        row.save()
        _audit(request, org_id=row.org_id, action=f"outlet_readiness_{self.action_name}", target_type="food_beverage_outlet_readiness", target_id=str(row.id), metadata={"reason": ser.validated_data.get("reason", "")}, property_id=row.property_id)
        return Response(_readiness_dict(row))


class FBOutletReadinessStartView(FBOutletReadinessActionView):
    action_name = "start"


class FBOutletReadinessSubmitView(FBOutletReadinessActionView):
    action_name = "submit"


class FBOutletReadinessVerifyView(FBOutletReadinessActionView):
    action_name = "verify"


class FBOutletReadinessVoidView(FBOutletReadinessActionView):
    action_name = "void"


class FBTaskListCreateView(APIView):
    def post(self, request):
        ser = FBTaskCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        assigned_to = User.objects.filter(id=data.get("assigned_to"), org_id=data["org_id"]).first() if data.get("assigned_to") else None
        row = FoodBeverageTask.objects.create(
            org_id=data["org_id"],
            property_id=data.get("property_id"),
            outlet_id=data["outlet_id"],
            task_number=f"FB-{int(datetime.now().timestamp())}",
            title=data["title"],
            task_type=data["task_type"],
            priority=data["priority"],
            assigned_to=assigned_to,
            status="ASSIGNED" if assigned_to else "PENDING",
            due_at=data.get("due_at"),
        )
        _audit(request, org_id=row.org_id, action="fb_task_created", target_type="food_beverage_task", target_id=str(row.id), property_id=row.property_id)
        return Response(_task_dict(row), status=status.HTTP_201_CREATED)

    def get(self, request):
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        qs = FoodBeverageTask.objects.filter(org_id=org_id)
        if request.query_params.get("q"):
            q = request.query_params["q"].strip()
            qs = qs.filter(Q(task_number__icontains=q) | Q(title__icontains=q) | Q(outlet_id__icontains=q))
        for f in ["property_id", "outlet_id", "task_type", "priority", "status"]:
            if request.query_params.get(f):
                qs = qs.filter(**{f: request.query_params[f]})
        if request.query_params.get("staff_id"):
            qs = qs.filter(assigned_to_id=int(request.query_params["staff_id"]))
        if request.query_params.get("date_from"):
            qs = qs.filter(updated_at__date__gte=request.query_params["date_from"])
        if request.query_params.get("date_to"):
            qs = qs.filter(updated_at__date__lte=request.query_params["date_to"])
        total, page, page_size, rows = _paginate(qs.order_by("-updated_at"), request)
        return Response({"count": total, "page": page, "page_size": page_size, "results": [_task_dict(x) for x in rows]})


class FBTaskDetailView(APIView):
    def get(self, request, id: int):
        row = FoodBeverageTask.objects.filter(id=id, org_id=int(request.query_params.get("org_id", "0"))).first()
        if not row:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_task_dict(row))

    def patch(self, request, id: int):
        ser = FBTaskUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        row = FoodBeverageTask.objects.filter(id=id, org_id=data["org_id"]).first()
        if not row:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        for k, v in data.items():
            if k != "org_id":
                setattr(row, k, v)
        row.save()
        _audit(request, org_id=row.org_id, action="fb_task_updated", target_type="food_beverage_task", target_id=str(row.id), property_id=row.property_id)
        return Response(_task_dict(row))


class FBTaskAssignView(APIView):
    def post(self, request, id: int):
        ser = FBTaskAssignSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        row = FoodBeverageTask.objects.filter(id=id, org_id=data["org_id"]).first()
        if not row:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        assignee_id = data.get("assignee_id") or data.get("assignee")
        if not assignee_id:
            return Response({"detail": "assignee_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        assignee = User.objects.filter(id=assignee_id, org_id=row.org_id).first()
        if not assignee:
            return Response({"detail": "Assignee not found"}, status=status.HTTP_400_BAD_REQUEST)
        was_assigned = row.assigned_to_id is not None
        row.assigned_to = assignee
        row.status = "ASSIGNED"
        row.save(update_fields=["assigned_to", "status", "updated_at"])
        _audit(request, org_id=row.org_id, action="fb_task_reassigned" if was_assigned else "fb_task_assigned", target_type="food_beverage_task", target_id=str(row.id), metadata={"assignee_id": assignee.id, "reason": data.get("reason", "")}, property_id=row.property_id)
        return Response(_task_dict(row))


class FBTaskActionView(APIView):
    action_name = ""

    def post(self, request, id: int):
        ser = FBTaskActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        row = FoodBeverageTask.objects.filter(id=id, org_id=ser.validated_data["org_id"]).first()
        if not row:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        if self.action_name == "start":
            row.status = "IN_PROGRESS"
            row.started_at = timezone.now()
        elif self.action_name == "complete":
            row.status = "COMPLETED"
            row.completed_at = timezone.now()
        elif self.action_name == "cancel":
            row.status = "CANCELLED"
            row.cancelled_reason = ser.validated_data.get("reason", "")
        elif self.action_name == "void":
            row.status = "VOID"
            row.void_reason = ser.validated_data.get("reason", "")
        row.save()
        action_map = {
            "start": "fb_task_started",
            "complete": "fb_task_completed",
            "cancel": "fb_task_cancelled",
            "void": "fb_task_voided",
        }
        _audit(request, org_id=row.org_id, action=action_map[self.action_name], target_type="food_beverage_task", target_id=str(row.id), metadata={"reason": ser.validated_data.get("reason", "")}, property_id=row.property_id)
        return Response(_task_dict(row))


class FBTaskStartView(FBTaskActionView):
    action_name = "start"


class FBTaskCompleteView(FBTaskActionView):
    action_name = "complete"


class FBTaskCancelView(FBTaskActionView):
    action_name = "cancel"


class FBTaskVoidView(FBTaskActionView):
    action_name = "void"


class FBMetricsSummaryView(APIView):
    def get(self, request):
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        bq = FoodBeverageBreakfastCount.objects.filter(org_id=org_id)
        rq = FoodBeverageOutletReadiness.objects.filter(org_id=org_id)
        tq = FoodBeverageTask.objects.filter(org_id=org_id)
        expected = sum([x.expected_guest_count for x in bq])
        actual = sum([x.actual_guest_count for x in bq])
        variance = actual - expected
        pct = (variance / expected * 100) if expected else 0
        payload = {
            "expected_breakfast_count": expected,
            "actual_breakfast_count": actual,
            "variance_count": variance,
            "variance_percentage": pct,
            "complimentary_count": sum([x.complimentary_count for x in bq]),
            "paid_count": sum([x.paid_count for x in bq]),
            "no_show_count": sum([x.no_show_count for x in bq]),
            "outlet_ready_count": rq.filter(status__in=["READY", "VERIFIED"]).count(),
            "outlet_not_ready_count": rq.filter(status="NOT_READY").count(),
            "average_readiness_score": float(rq.aggregate(v=Avg("checklist_score"))["v"] or 0),
            "total_tasks": tq.count(),
            "completed_tasks": tq.filter(status="COMPLETED").count(),
            "overdue_tasks": tq.filter(due_at__lt=timezone.now()).exclude(status__in=["COMPLETED", "CANCELLED", "VOID"]).count(),
            "average_task_completion_time": 0,
        }
        _audit(request, org_id=org_id, action="fb_metrics_viewed", target_type="food_beverage_metrics", target_id="summary")
        return Response(payload)


class FBMetricsBreakfastView(APIView):
    def get(self, request):
        org_id = int(request.query_params.get("org_id", "0"))
        rows = FoodBeverageBreakfastCount.objects.filter(org_id=org_id).order_by("service_date")
        return Response([{"date": str(x.service_date), "value": x.actual_guest_count} for x in rows])


class FBMetricsOutletReadinessView(APIView):
    def get(self, request):
        org_id = int(request.query_params.get("org_id", "0"))
        rows = FoodBeverageOutletReadiness.objects.filter(org_id=org_id).values("status").annotate(value=Count("id")).order_by("status")
        return Response([{"status": x["status"], "value": x["value"]} for x in rows])


class FBMetricsTasksView(APIView):
    def get(self, request):
        org_id = int(request.query_params.get("org_id", "0"))
        rows = FoodBeverageTask.objects.filter(org_id=org_id).values("status").annotate(value=Count("id")).order_by("status")
        return Response([{"label": x["status"], "value": x["value"]} for x in rows])


class FBAuditLogsView(APIView):
    def get(self, request):
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        qs = AuditLog.objects.filter(org_id=org_id, target_type__in=["food_beverage_breakfast_count", "food_beverage_outlet_readiness", "food_beverage_task", "food_beverage_metrics"])
        if request.query_params.get("action"):
            qs = qs.filter(action__icontains=request.query_params["action"])
        if request.query_params.get("target_type"):
            qs = qs.filter(target_type=request.query_params["target_type"])
        if request.query_params.get("actor_user_id"):
            qs = qs.filter(actor_user_id=int(request.query_params["actor_user_id"]))
        if request.query_params.get("date_from"):
            qs = qs.filter(created_at__date__gte=request.query_params["date_from"])
        if request.query_params.get("date_to"):
            qs = qs.filter(created_at__date__lte=request.query_params["date_to"])
        total, page, page_size, rows = _paginate(qs.order_by("-created_at"), request)
        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": [{
                "id": x.id,
                "created_at": x.created_at,
                "actor_user_id": x.actor_user_id,
                "action": x.action,
                "target_type": x.target_type,
                "target_id": x.target_id,
                "metadata": x.metadata_json,
            } for x in rows],
        })
