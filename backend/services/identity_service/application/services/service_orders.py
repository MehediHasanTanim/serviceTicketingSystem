from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from infrastructure.db.core.models import (
    ServiceOrder,
    ServiceOrderAssignmentHistory,
    ServiceOrderAttachment,
    ServiceOrderRemark,
    ServiceOrderStatusHistory,
    User,
)


class ServiceOrderError(Exception):
    pass


class ServiceOrderValidationError(ServiceOrderError):
    pass


class ServiceOrderNotFoundError(ServiceOrderError):
    pass


class ServiceOrderTransitionError(ServiceOrderError):
    pass


class LifecycleRuleValidator:
    ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        ServiceOrder.STATUS_OPEN: {ServiceOrder.STATUS_ASSIGNED, ServiceOrder.STATUS_VOID},
        ServiceOrder.STATUS_ASSIGNED: {
            ServiceOrder.STATUS_IN_PROGRESS,
            ServiceOrder.STATUS_DEFERRED,
            ServiceOrder.STATUS_VOID,
        },
        ServiceOrder.STATUS_IN_PROGRESS: {
            ServiceOrder.STATUS_ON_HOLD,
            ServiceOrder.STATUS_COMPLETED,
            ServiceOrder.STATUS_DEFERRED,
            ServiceOrder.STATUS_VOID,
        },
        ServiceOrder.STATUS_ON_HOLD: {
            ServiceOrder.STATUS_IN_PROGRESS,
            ServiceOrder.STATUS_DEFERRED,
            ServiceOrder.STATUS_VOID,
        },
        ServiceOrder.STATUS_DEFERRED: {ServiceOrder.STATUS_ASSIGNED, ServiceOrder.STATUS_VOID},
        ServiceOrder.STATUS_COMPLETED: set(),
        ServiceOrder.STATUS_VOID: set(),
    }

    def validate(self, from_status: str, to_status: str) -> None:
        allowed = self.ALLOWED_TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            raise ServiceOrderTransitionError(
                f"Invalid transition from {from_status} to {to_status}"
            )


class CostCalculator:
    ZERO = Decimal("0.00")

    def _norm(self, value: Decimal | str | int | float | None) -> Decimal:
        val = Decimal(str(value if value is not None else self.ZERO))
        if val < self.ZERO:
            raise ServiceOrderValidationError("Cost values cannot be negative")
        return val.quantize(Decimal("0.01"))

    def calculate(
        self,
        *,
        parts_cost: Decimal | str | int | float | None,
        labor_cost: Decimal | str | int | float | None,
        compensation_cost: Decimal | str | int | float | None,
    ) -> dict[str, Decimal]:
        parts = self._norm(parts_cost)
        labor = self._norm(labor_cost)
        compensation = self._norm(compensation_cost)
        total = (parts + labor + compensation).quantize(Decimal("0.01"))
        return {
            "parts_cost": parts,
            "labor_cost": labor,
            "compensation_cost": compensation,
            "total_cost": total,
        }


@dataclass
class ServiceOrderFilters:
    org_id: int
    status: str | None = None
    priority: str | None = None
    type: str | None = None
    assigned_to: int | None = None
    customer_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None


class ServiceOrderRepository:
    def create(self, **kwargs) -> ServiceOrder:
        return ServiceOrder.objects.create(**kwargs)

    def get_for_org(self, order_id: int, org_id: int) -> ServiceOrder:
        try:
            return ServiceOrder.objects.get(id=order_id, org_id=org_id, is_deleted=False)
        except ServiceOrder.DoesNotExist as exc:
            raise ServiceOrderNotFoundError("Service order not found") from exc

    def list(self, filters: ServiceOrderFilters) -> QuerySet[ServiceOrder]:
        qs = ServiceOrder.objects.filter(org_id=filters.org_id, is_deleted=False)
        if filters.status:
            qs = qs.filter(status=filters.status)
        if filters.priority:
            qs = qs.filter(priority=filters.priority)
        if filters.type:
            qs = qs.filter(type=filters.type)
        if filters.assigned_to:
            qs = qs.filter(assigned_to_id=filters.assigned_to)
        if filters.customer_id:
            qs = qs.filter(customer_id=filters.customer_id)
        if filters.date_from:
            qs = qs.filter(created_at__date__gte=filters.date_from)
        if filters.date_to:
            qs = qs.filter(created_at__date__lte=filters.date_to)
        return qs

    def save(self, order: ServiceOrder, *, update_fields: list[str] | None = None) -> ServiceOrder:
        order.version += 1
        if update_fields is not None and "version" not in update_fields:
            update_fields = [*update_fields, "version"]
        order.save(update_fields=update_fields)
        return order

    def soft_delete(self, order: ServiceOrder) -> None:
        order.is_deleted = True
        order.deleted_at = timezone.now()
        self.save(order, update_fields=["is_deleted", "deleted_at"])


class AssignmentHistoryRepository:
    def create(
        self,
        *,
        service_order: ServiceOrder,
        previous_assignee: User | None,
        new_assignee: User,
        changed_by: User,
        reason: str = "",
    ) -> ServiceOrderAssignmentHistory:
        return ServiceOrderAssignmentHistory.objects.create(
            service_order=service_order,
            previous_assignee=previous_assignee,
            new_assignee=new_assignee,
            changed_by=changed_by,
            reason=reason or "",
        )


class ServiceOrderService:
    def __init__(
        self,
        *,
        repository: ServiceOrderRepository | None = None,
        assignment_history_repository: AssignmentHistoryRepository | None = None,
        lifecycle_rule_validator: LifecycleRuleValidator | None = None,
        cost_calculator: CostCalculator | None = None,
    ) -> None:
        self.repository = repository or ServiceOrderRepository()
        self.assignment_history_repository = assignment_history_repository or AssignmentHistoryRepository()
        self.lifecycle_rule_validator = lifecycle_rule_validator or LifecycleRuleValidator()
        self.cost_calculator = cost_calculator or CostCalculator()

    def _generate_ticket_number(self, order_id: int) -> str:
        return f"SO-{order_id:08d}"

    @transaction.atomic
    def create_order(self, *, created_by: User, org_id: int, **payload) -> ServiceOrder:
        costs = self.cost_calculator.calculate(
            parts_cost=payload.get("parts_cost", Decimal("0")),
            labor_cost=payload.get("labor_cost", Decimal("0")),
            compensation_cost=payload.get("compensation_cost", Decimal("0")),
        )
        order = self.repository.create(
            org_id=org_id,
            ticket_number=f"TEMP-{timezone.now().timestamp()}",
            created_by=created_by,
            assigned_to=payload.get("assigned_to"),
            title=payload["title"],
            description=payload.get("description", ""),
            customer_id=payload["customer_id"],
            asset_id=payload.get("asset_id"),
            priority=payload.get("priority", ServiceOrder.PRIORITY_MEDIUM),
            type=payload.get("type", ServiceOrder.TYPE_OTHER),
            status=ServiceOrder.STATUS_OPEN,
            due_date=payload.get("due_date"),
            scheduled_at=payload.get("scheduled_at"),
            estimated_cost=payload.get("estimated_cost", Decimal("0")),
            completed_at=None,
            **costs,
        )
        order.ticket_number = self._generate_ticket_number(order.id)
        self.repository.save(order, update_fields=["ticket_number"])
        if order.assigned_to_id:
            self._transition(order=order, to_status=ServiceOrder.STATUS_ASSIGNED, actor=created_by, note="")
            self.assignment_history_repository.create(
                service_order=order,
                previous_assignee=None,
                new_assignee=order.assigned_to,
                changed_by=created_by,
                reason="Initial assignment",
            )
        return order

    def list_orders(self, *, filters: ServiceOrderFilters) -> QuerySet[ServiceOrder]:
        return self.repository.list(filters)

    def get_order(self, *, order_id: int, org_id: int) -> ServiceOrder:
        return self.repository.get_for_org(order_id, org_id)

    @transaction.atomic
    def update_order(self, *, order: ServiceOrder, **payload) -> ServiceOrder:
        for key in [
            "title",
            "description",
            "customer_id",
            "asset_id",
            "priority",
            "type",
            "due_date",
            "scheduled_at",
            "estimated_cost",
        ]:
            if key in payload:
                setattr(order, key, payload[key])
        self.repository.save(order)
        return order

    @transaction.atomic
    def update_costs(self, *, order: ServiceOrder, parts_cost, labor_cost, compensation_cost) -> ServiceOrder:
        costs = self.cost_calculator.calculate(
            parts_cost=parts_cost,
            labor_cost=labor_cost,
            compensation_cost=compensation_cost,
        )
        order.parts_cost = costs["parts_cost"]
        order.labor_cost = costs["labor_cost"]
        order.compensation_cost = costs["compensation_cost"]
        order.total_cost = costs["total_cost"]
        self.repository.save(order)
        return order

    @transaction.atomic
    def assign(self, *, order: ServiceOrder, assignee: User, actor: User, reason: str = "") -> ServiceOrder:
        previous_assignee = order.assigned_to
        if previous_assignee and previous_assignee.id == assignee.id:
            return order
        order.assigned_to = assignee
        self._transition(order=order, to_status=ServiceOrder.STATUS_ASSIGNED, actor=actor, note=reason)
        self.assignment_history_repository.create(
            service_order=order,
            previous_assignee=previous_assignee,
            new_assignee=assignee,
            changed_by=actor,
            reason=reason,
        )
        return order

    @transaction.atomic
    def transition(self, *, order: ServiceOrder, to_status: str, actor: User, note: str = "") -> ServiceOrder:
        self._transition(order=order, to_status=to_status, actor=actor, note=note)
        return order

    def _transition(self, *, order: ServiceOrder, to_status: str, actor: User, note: str) -> None:
        from_status = order.status
        self.lifecycle_rule_validator.validate(from_status, to_status)
        order.status = to_status
        if to_status == ServiceOrder.STATUS_COMPLETED:
            order.completed_at = timezone.now()
        self.repository.save(order)
        ServiceOrderStatusHistory.objects.create(
            service_order=order,
            from_status=from_status,
            to_status=to_status,
            changed_by=actor,
            note=note or "",
        )

    @transaction.atomic
    def add_attachment(self, *, order: ServiceOrder, file_name: str, storage_key: str, actor: User) -> ServiceOrderAttachment:
        return ServiceOrderAttachment.objects.create(
            service_order=order,
            file_name=file_name,
            storage_key=storage_key,
            uploaded_by=actor,
        )

    @transaction.atomic
    def add_remark(self, *, order: ServiceOrder, text: str, actor: User, is_internal: bool = True) -> ServiceOrderRemark:
        return ServiceOrderRemark.objects.create(
            service_order=order,
            text=text,
            author=actor,
            is_internal=is_internal,
        )

    def list_remarks(self, *, order: ServiceOrder) -> QuerySet[ServiceOrderRemark]:
        return ServiceOrderRemark.objects.filter(service_order=order).order_by("-created_at")

    @transaction.atomic
    def soft_delete(self, *, order: ServiceOrder) -> None:
        self.repository.soft_delete(order)
