from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.services.audit_logging import AuditContext
from application.services.service_orders import (
    ServiceOrderFilters,
    ServiceOrderNotFoundError,
    ServiceOrderService,
    ServiceOrderTransitionError,
    ServiceOrderValidationError,
)
from infrastructure.db.core.models import RolePermission, ServiceOrder, User, UserRole
from infrastructure.services.audit_logging import get_audit_logger
from interfaces.api.serializers import (
    ServiceOrderAssignSerializer,
    ServiceOrderAttachmentSerializer,
    ServiceOrderCostUpdateSerializer,
    ServiceOrderCreateSerializer,
    ServiceOrderRemarkSerializer,
    ServiceOrderResponseSerializer,
    ServiceOrderTransitionSerializer,
    ServiceOrderUpdateSerializer,
)


def _get_request_ip(request) -> str:
    if hasattr(request, "audit_context"):
        return request.audit_context.get("ip_address", "")
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _build_audit_context(request, org_id: int, *, actor_user=None) -> AuditContext:
    if hasattr(request, "audit_context"):
        meta = request.audit_context
        return AuditContext(
            org_id=org_id,
            property_id=None,
            actor_user_id=getattr(actor_user, "id", None),
            ip_address=meta.get("ip_address", ""),
            user_agent=meta.get("user_agent", ""),
        )
    return AuditContext(
        org_id=org_id,
        property_id=None,
        actor_user_id=getattr(actor_user, "id", None),
        ip_address=_get_request_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )


def _audit_action(
    request,
    *,
    org_id: int,
    action: str,
    target_type: str,
    target_id: str,
    metadata: dict | None = None,
    actor_user=None,
) -> None:
    logger = get_audit_logger()
    context = _build_audit_context(request, org_id, actor_user=actor_user)
    logger.log_action(
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        metadata=metadata or {},
        context=context,
    )


def _has_permission(user, code: str) -> bool:
    if not user:
        return False
    if hasattr(user, "is_authenticated") and not user.is_authenticated:
        return False
    if UserRole.objects.filter(user=user, role__name__iexact="super admin").exists():
        return True
    return RolePermission.objects.filter(role__user_roles__user=user, permission__code=code).exists()


def _order_to_dict(order: ServiceOrder) -> dict:
    return {
        "id": order.id,
        "org_id": order.org_id,
        "ticket_number": order.ticket_number,
        "title": order.title,
        "description": order.description,
        "customer_id": order.customer_id,
        "asset_id": order.asset_id,
        "created_by": order.created_by_id,
        "assigned_to": order.assigned_to_id,
        "priority": order.priority,
        "type": order.type,
        "status": order.status,
        "due_date": order.due_date,
        "scheduled_at": order.scheduled_at,
        "completed_at": order.completed_at,
        "estimated_cost": order.estimated_cost,
        "parts_cost": order.parts_cost,
        "labor_cost": order.labor_cost,
        "compensation_cost": order.compensation_cost,
        "total_cost": order.total_cost,
        "version": order.version,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


def _order_snapshot(order: ServiceOrder) -> dict:
    return {
        "id": order.id,
        "ticket_number": order.ticket_number,
        "title": order.title,
        "status": order.status,
        "priority": order.priority,
        "type": order.type,
        "assigned_to": order.assigned_to_id,
        "total_cost": str(order.total_cost),
    }


class ServiceOrderListCreateView(APIView):
    service = ServiceOrderService()

    def post(self, request):
        if not _has_permission(request.user, "service_orders.manage"):
            return Response({"detail": "Permission required: service_orders.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ServiceOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        assignee = None
        if data.get("assigned_to"):
            assignee = User.objects.filter(id=data["assigned_to"], org_id=data["org_id"]).first()
            if not assignee:
                return Response({"detail": "Assignee not found in organization"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            order = self.service.create_order(
                created_by=request.user,
                org_id=data["org_id"],
                assigned_to=assignee,
                **{k: v for k, v in data.items() if k not in {"org_id", "assigned_to"}},
            )
        except ServiceOrderValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit_action(
            request,
            org_id=order.org_id,
            action="service_order.created",
            target_type="service_order",
            target_id=str(order.id),
            metadata=_order_snapshot(order),
            actor_user=request.user,
        )
        return Response(ServiceOrderResponseSerializer(_order_to_dict(order)).data, status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "service_orders.view"):
            return Response({"detail": "Permission required: service_orders.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = request.query_params.get("org_id")
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        filters = ServiceOrderFilters(
            org_id=int(org_id),
            status=request.query_params.get("status"),
            priority=request.query_params.get("priority"),
            type=request.query_params.get("type"),
            assigned_to=int(request.query_params["assigned_to"]) if request.query_params.get("assigned_to") else None,
            customer_id=int(request.query_params["customer_id"]) if request.query_params.get("customer_id") else None,
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
        )
        if isinstance(filters.date_from, str):
            from django.utils.dateparse import parse_date
            filters.date_from = parse_date(filters.date_from)
        if isinstance(filters.date_to, str):
            from django.utils.dateparse import parse_date
            filters.date_to = parse_date(filters.date_to)
        qs = self.service.list_orders(filters=filters)
        search = request.query_params.get("q", "").strip()
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(ticket_number__icontains=search))
        sort_by = request.query_params.get("sort_by", "created_at")
        sort_dir = request.query_params.get("sort_dir", "desc").lower()
        allowed_sorts = {"id", "ticket_number", "priority", "type", "status", "created_at", "updated_at", "due_date"}
        if sort_by not in allowed_sorts:
            sort_by = "created_at"
        prefix = "-" if sort_dir == "desc" else ""
        page = max(int(request.query_params.get("page", "1") or "1"), 1)
        page_size = min(max(int(request.query_params.get("page_size", "10") or "10"), 1), 100)
        total = qs.count()
        offset = (page - 1) * page_size
        rows = qs.order_by(f"{prefix}{sort_by}")[offset:offset + page_size]
        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": [ServiceOrderResponseSerializer(_order_to_dict(row)).data for row in rows],
            }
        )


class ServiceOrderDetailView(APIView):
    service = ServiceOrderService()

    def get_object(self, order_id: int, org_id: int):
        return self.service.get_order(order_id=order_id, org_id=org_id)

    def get(self, request, order_id: int):
        if not _has_permission(request.user, "service_orders.view"):
            return Response({"detail": "Permission required: service_orders.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            order = self.get_object(order_id, org_id)
        except ServiceOrderNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(ServiceOrderResponseSerializer(_order_to_dict(order)).data)

    def patch(self, request, order_id: int):
        return self._update(request, order_id, partial=True)

    def put(self, request, order_id: int):
        return self._update(request, order_id, partial=False)

    def _update(self, request, order_id: int, partial: bool):
        if not _has_permission(request.user, "service_orders.manage"):
            return Response({"detail": "Permission required: service_orders.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        try:
            order = self.get_object(order_id, org_id)
        except ServiceOrderNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        serializer = ServiceOrderUpdateSerializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        before = _order_snapshot(order)
        updated = self.service.update_order(order=order, **serializer.validated_data)
        _audit_action(
            request,
            org_id=updated.org_id,
            action="service_order.updated",
            target_type="service_order",
            target_id=str(updated.id),
            metadata={"before": before, "after": _order_snapshot(updated)},
            actor_user=request.user,
        )
        return Response(ServiceOrderResponseSerializer(_order_to_dict(updated)).data)

    def delete(self, request, order_id: int):
        if not _has_permission(request.user, "service_orders.manage"):
            return Response({"detail": "Permission required: service_orders.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            order = self.get_object(order_id, org_id)
        except ServiceOrderNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        snapshot = _order_snapshot(order)
        self.service.soft_delete(order=order)
        _audit_action(
            request,
            org_id=order.org_id,
            action="service_order.deleted",
            target_type="service_order",
            target_id=str(order.id),
            metadata=snapshot,
            actor_user=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServiceOrderAssignView(APIView):
    service = ServiceOrderService()

    def post(self, request, order_id: int):
        if not _has_permission(request.user, "service_orders.manage"):
            return Response({"detail": "Permission required: service_orders.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ServiceOrderAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        try:
            order = self.service.get_order(order_id=order_id, org_id=org_id)
        except ServiceOrderNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        assignee = User.objects.filter(id=serializer.validated_data["assignee_id"], org_id=org_id).first()
        if not assignee:
            return Response({"detail": "Assignee not found in organization"}, status=status.HTTP_400_BAD_REQUEST)
        had_assignee = bool(order.assigned_to_id)
        try:
            order = self.service.assign(
                order=order,
                assignee=assignee,
                actor=request.user,
                reason=serializer.validated_data.get("reason", ""),
            )
        except ServiceOrderTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit_action(
            request,
            org_id=order.org_id,
            action="service_order.reassigned" if had_assignee else "service_order.assigned",
            target_type="service_order",
            target_id=str(order.id),
            metadata={
                "assignee_id": assignee.id,
                "reason": serializer.validated_data.get("reason", ""),
            },
            actor_user=request.user,
        )
        return Response(ServiceOrderResponseSerializer(_order_to_dict(order)).data)


class ServiceOrderTransitionView(APIView):
    service = ServiceOrderService()
    transition_status: str = ""

    def post(self, request, order_id: int):
        if not _has_permission(request.user, "service_orders.manage"):
            return Response({"detail": "Permission required: service_orders.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ServiceOrderTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        try:
            order = self.service.get_order(order_id=order_id, org_id=org_id)
        except ServiceOrderNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        try:
            updated = self.service.transition(
                order=order,
                to_status=self.transition_status,
                actor=request.user,
                note=serializer.validated_data.get("note", ""),
            )
        except ServiceOrderTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit_action(
            request,
            org_id=updated.org_id,
            action=f"service_order.transitioned.{self.transition_status.lower()}",
            target_type="service_order",
            target_id=str(updated.id),
            metadata={"status": updated.status, "note": serializer.validated_data.get("note", "")},
            actor_user=request.user,
        )
        return Response(ServiceOrderResponseSerializer(_order_to_dict(updated)).data)


class ServiceOrderStartView(ServiceOrderTransitionView):
    transition_status = ServiceOrder.STATUS_IN_PROGRESS


class ServiceOrderHoldView(ServiceOrderTransitionView):
    transition_status = ServiceOrder.STATUS_ON_HOLD


class ServiceOrderCompleteView(ServiceOrderTransitionView):
    transition_status = ServiceOrder.STATUS_COMPLETED


class ServiceOrderDeferView(ServiceOrderTransitionView):
    transition_status = ServiceOrder.STATUS_DEFERRED


class ServiceOrderVoidView(ServiceOrderTransitionView):
    transition_status = ServiceOrder.STATUS_VOID


class ServiceOrderAttachmentView(APIView):
    service = ServiceOrderService()

    def get(self, request, order_id: int):
        if not _has_permission(request.user, "service_orders.view"):
            return Response({"detail": "Permission required: service_orders.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            order = self.service.get_order(order_id=order_id, org_id=org_id)
        except ServiceOrderNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        attachments = order.attachments.order_by("-uploaded_at")
        return Response(
            {
                "count": attachments.count(),
                "results": [
                    {
                        "id": row.id,
                        "file_name": row.file_name,
                        "storage_key": row.storage_key,
                        "uploaded_by": row.uploaded_by_id,
                        "uploaded_at": row.uploaded_at,
                    }
                    for row in attachments
                ],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, order_id: int):
        if not _has_permission(request.user, "service_orders.manage"):
            return Response({"detail": "Permission required: service_orders.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ServiceOrderAttachmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        try:
            order = self.service.get_order(order_id=order_id, org_id=org_id)
        except ServiceOrderNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        attachment = self.service.add_attachment(order=order, actor=request.user, **serializer.validated_data)
        _audit_action(
            request,
            org_id=order.org_id,
            action="service_order.attachment_added",
            target_type="service_order",
            target_id=str(order.id),
            metadata={"attachment_id": attachment.id, "file_name": attachment.file_name},
            actor_user=request.user,
        )
        return Response(
            {
                "id": attachment.id,
                "file_name": attachment.file_name,
                "storage_key": attachment.storage_key,
                "uploaded_by": attachment.uploaded_by_id,
                "uploaded_at": attachment.uploaded_at,
            },
            status=status.HTTP_201_CREATED,
        )


class ServiceOrderRemarkView(APIView):
    service = ServiceOrderService()

    def post(self, request, order_id: int):
        if not _has_permission(request.user, "service_orders.manage"):
            return Response({"detail": "Permission required: service_orders.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ServiceOrderRemarkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        try:
            order = self.service.get_order(order_id=order_id, org_id=org_id)
        except ServiceOrderNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        remark = self.service.add_remark(order=order, actor=request.user, **serializer.validated_data)
        _audit_action(
            request,
            org_id=order.org_id,
            action="service_order.remark_added",
            target_type="service_order",
            target_id=str(order.id),
            metadata={"remark_id": remark.id, "is_internal": remark.is_internal},
            actor_user=request.user,
        )
        return Response(
            {
                "id": remark.id,
                "text": remark.text,
                "author": remark.author_id,
                "is_internal": remark.is_internal,
                "created_at": remark.created_at,
            },
            status=status.HTTP_201_CREATED,
        )

    def get(self, request, order_id: int):
        if not _has_permission(request.user, "service_orders.view"):
            return Response({"detail": "Permission required: service_orders.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            order = self.service.get_order(order_id=order_id, org_id=org_id)
        except ServiceOrderNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        remarks = self.service.list_remarks(order=order)
        return Response(
            {
                "count": remarks.count(),
                "results": [
                    {
                        "id": row.id,
                        "text": row.text,
                        "author": row.author_id,
                        "is_internal": row.is_internal,
                        "created_at": row.created_at,
                    }
                    for row in remarks
                ],
            }
        )


class ServiceOrderCostUpdateView(APIView):
    service = ServiceOrderService()

    def patch(self, request, order_id: int):
        if not _has_permission(request.user, "service_orders.manage"):
            return Response({"detail": "Permission required: service_orders.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ServiceOrderCostUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        try:
            order = self.service.get_order(order_id=order_id, org_id=org_id)
        except ServiceOrderNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        try:
            updated = self.service.update_costs(order=order, **serializer.validated_data)
        except ServiceOrderValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit_action(
            request,
            org_id=updated.org_id,
            action="service_order.costs_updated",
            target_type="service_order",
            target_id=str(updated.id),
            metadata={
                "parts_cost": str(updated.parts_cost),
                "labor_cost": str(updated.labor_cost),
                "compensation_cost": str(updated.compensation_cost),
                "total_cost": str(updated.total_cost),
            },
            actor_user=request.user,
        )
        return Response(ServiceOrderResponseSerializer(_order_to_dict(updated)).data)
