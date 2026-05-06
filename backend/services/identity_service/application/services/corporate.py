from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.db import IntegrityError, transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from infrastructure.db.core.models import (
    ApprovalHistory,
    ApprovalRequest,
    CAPEXRequest,
    CorporateContract,
    PurchaseOrder,
    PurchaseOrderLineItem,
    Supplier,
    User,
)


class CorporateError(Exception):
    pass


class CorporateValidationError(CorporateError):
    pass


class CorporateNotFoundError(CorporateError):
    pass


@dataclass
class SupplierFilters:
    org_id: int
    category: str | None = None
    status: str | None = None
    rating: int | None = None
    q: str | None = None


@dataclass
class ContractFilters:
    org_id: int
    supplier_id: int | None = None
    status: str | None = None
    contract_type: str | None = None
    owner_id: int | None = None
    expiry_from: str | None = None
    expiry_to: str | None = None


@dataclass
class POFilters:
    org_id: int
    status: str | None = None
    supplier_id: int | None = None


@dataclass
class CAPEXFilters:
    org_id: int
    status: str | None = None
    category: str | None = None


class PurchaseOrderCalculator:
    ZERO = Decimal("0.00")

    def _d(self, value) -> Decimal:
        return Decimal(str(value if value is not None else "0"))

    def _money(self, value) -> Decimal:
        return self._d(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def line_total(self, *, quantity, unit_price, tax_rate, discount_amount) -> Decimal:
        q = self._d(quantity)
        p = self._money(unit_price)
        t = self._d(tax_rate)
        d = self._money(discount_amount)
        if q <= 0:
            raise CorporateValidationError("quantity must be positive")
        if p <= 0:
            raise CorporateValidationError("unit_price must be positive")
        if t < 0:
            raise CorporateValidationError("tax_rate must be non-negative")
        if d < 0:
            raise CorporateValidationError("discount_amount must be non-negative")
        base = (q * p).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tax = (base * t).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = (base + tax - d).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if total < self.ZERO:
            raise CorporateValidationError("line_total cannot be negative")
        return total

    def totals(self, line_items: list[dict]) -> dict[str, Decimal]:
        subtotal = self.ZERO
        tax_amount = self.ZERO
        discount_amount = self.ZERO
        total_amount = self.ZERO
        for li in line_items:
            q = self._d(li["quantity"])
            p = self._money(li["unit_price"])
            tr = self._d(li.get("tax_rate") or 0)
            disc = self._money(li.get("discount_amount") or 0)
            base = (q * p).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            tax = (base * tr).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            lt = self.line_total(quantity=q, unit_price=p, tax_rate=tr, discount_amount=disc)
            subtotal += base
            tax_amount += tax
            discount_amount += disc
            total_amount += lt
        return {
            "subtotal": subtotal.quantize(Decimal("0.01")),
            "tax_amount": tax_amount.quantize(Decimal("0.01")),
            "discount_amount": discount_amount.quantize(Decimal("0.01")),
            "total_amount": total_amount.quantize(Decimal("0.01")),
        }


class SupplierRepository:
    def create(self, **kwargs) -> Supplier:
        return Supplier.objects.create(**kwargs)

    def get_for_org(self, *, org_id: int, supplier_id: int) -> Supplier:
        row = Supplier.objects.filter(org_id=org_id, id=supplier_id).first()
        if not row:
            raise CorporateNotFoundError("Supplier not found")
        return row

    def list(self, filters: SupplierFilters) -> QuerySet[Supplier]:
        qs = Supplier.objects.filter(org_id=filters.org_id)
        if filters.category:
            qs = qs.filter(category__iexact=filters.category)
        if filters.status:
            qs = qs.filter(status=filters.status)
        if filters.rating:
            qs = qs.filter(rating=filters.rating)
        if filters.q:
            qs = qs.filter(Q(name__icontains=filters.q) | Q(supplier_code__icontains=filters.q))
        return qs


class ContractRepository:
    def create(self, **kwargs) -> CorporateContract:
        return CorporateContract.objects.create(**kwargs)

    def get_for_org(self, *, org_id: int, contract_id: int) -> CorporateContract:
        row = CorporateContract.objects.filter(org_id=org_id, id=contract_id).first()
        if not row:
            raise CorporateNotFoundError("Contract not found")
        return row

    def list(self, filters: ContractFilters) -> QuerySet[CorporateContract]:
        qs = CorporateContract.objects.filter(org_id=filters.org_id)
        if filters.supplier_id:
            qs = qs.filter(supplier_id=filters.supplier_id)
        if filters.status:
            qs = qs.filter(status=filters.status)
        if filters.contract_type:
            qs = qs.filter(contract_type__iexact=filters.contract_type)
        if filters.owner_id:
            qs = qs.filter(owner_id=filters.owner_id)
        if filters.expiry_from:
            qs = qs.filter(expiry_date__gte=filters.expiry_from)
        if filters.expiry_to:
            qs = qs.filter(expiry_date__lte=filters.expiry_to)
        return qs


class PurchaseOrderRepository:
    def create(self, **kwargs) -> PurchaseOrder:
        return PurchaseOrder.objects.create(**kwargs)

    def get_for_org(self, *, org_id: int, po_id: int) -> PurchaseOrder:
        row = PurchaseOrder.objects.filter(org_id=org_id, id=po_id).first()
        if not row:
            raise CorporateNotFoundError("Purchase order not found")
        return row

    def list(self, filters: POFilters) -> QuerySet[PurchaseOrder]:
        qs = PurchaseOrder.objects.filter(org_id=filters.org_id)
        if filters.status:
            qs = qs.filter(status=filters.status)
        if filters.supplier_id:
            qs = qs.filter(supplier_id=filters.supplier_id)
        return qs


class PurchaseOrderLineItemRepository:
    def replace(self, *, po: PurchaseOrder, line_items: list[dict], calculator: PurchaseOrderCalculator) -> list[PurchaseOrderLineItem]:
        PurchaseOrderLineItem.objects.filter(purchase_order=po).delete()
        rows = []
        for item in line_items:
            lt = calculator.line_total(
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                tax_rate=item.get("tax_rate", 0),
                discount_amount=item.get("discount_amount", 0),
            )
            rows.append(
                PurchaseOrderLineItem.objects.create(
                    purchase_order=po,
                    item_name=item["item_name"],
                    description=item.get("description", ""),
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    tax_rate=item.get("tax_rate", 0),
                    discount_amount=item.get("discount_amount", 0),
                    line_total=lt,
                )
            )
        return rows


class CAPEXRepository:
    def create(self, **kwargs) -> CAPEXRequest:
        return CAPEXRequest.objects.create(**kwargs)

    def get_for_org(self, *, org_id: int, capex_id: int) -> CAPEXRequest:
        row = CAPEXRequest.objects.filter(org_id=org_id, id=capex_id).first()
        if not row:
            raise CorporateNotFoundError("CAPEX request not found")
        return row

    def list(self, filters: CAPEXFilters) -> QuerySet[CAPEXRequest]:
        qs = CAPEXRequest.objects.filter(org_id=filters.org_id)
        if filters.status:
            qs = qs.filter(status=filters.status)
        if filters.category:
            qs = qs.filter(category__iexact=filters.category)
        return qs


class ApprovalWorkflowRepository:
    def create(self, **kwargs) -> ApprovalRequest:
        return ApprovalRequest.objects.create(**kwargs)

    def pending(self, *, org_id: int, entity_type: str, entity_id: int) -> QuerySet[ApprovalRequest]:
        return ApprovalRequest.objects.filter(
            org_id=org_id,
            entity_type=entity_type,
            entity_id=entity_id,
            status=ApprovalRequest.STATUS_PENDING,
        ).order_by("approval_level", "id")

    def level_status(self, *, org_id: int, entity_type: str, entity_id: int, level: int) -> QuerySet[ApprovalRequest]:
        return ApprovalRequest.objects.filter(
            org_id=org_id,
            entity_type=entity_type,
            entity_id=entity_id,
            approval_level=level,
        )


class ApprovalWorkflowService:
    PO_AUTO_APPROVE_THRESHOLD = Decimal("500.00")
    CAPEX_HIGH_VALUE_THRESHOLD = Decimal("5000.00")

    def __init__(self, repo: ApprovalWorkflowRepository | None = None):
        self.repo = repo or ApprovalWorkflowRepository()

    def approval_levels_for_po(self, total_amount: Decimal) -> list[int]:
        if total_amount <= self.PO_AUTO_APPROVE_THRESHOLD:
            return []
        if total_amount <= self.CAPEX_HIGH_VALUE_THRESHOLD:
            return [1]
        return [1, 2]

    def approval_levels_for_capex(self, estimated_amount: Decimal) -> list[int]:
        if estimated_amount <= self.CAPEX_HIGH_VALUE_THRESHOLD:
            return [1]
        return [1, 2]

    @transaction.atomic
    def create_approval_requests(
        self,
        *,
        org_id: int,
        entity_type: str,
        entity_id: int,
        levels: list[int],
        approvers_by_level: dict[int, User],
    ) -> list[ApprovalRequest]:
        rows: list[ApprovalRequest] = []
        for lvl in levels:
            approver = approvers_by_level.get(lvl)
            if not approver:
                raise CorporateValidationError(f"approver missing for level {lvl}")
            exists_pending = self.repo.pending(org_id=org_id, entity_type=entity_type, entity_id=entity_id).filter(approval_level=lvl).exists()
            if exists_pending:
                continue
            try:
                row = self.repo.create(
                    org_id=org_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    approval_level=lvl,
                    approver=approver,
                    status=ApprovalRequest.STATUS_PENDING,
                )
                rows.append(row)
                ApprovalHistory.objects.create(
                    org_id=org_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    approval_level=lvl,
                    approver=approver,
                    status=ApprovalRequest.STATUS_PENDING,
                    request_ref=row,
                )
            except IntegrityError:
                continue
        return rows

    @transaction.atomic
    def decide(
        self,
        *,
        org_id: int,
        entity_type: str,
        entity_id: int,
        level: int,
        approver: User,
        decision: str,
        comment: str,
        requester_id: int | None,
        allow_self_approve: bool = False,
    ) -> ApprovalRequest:
        row = self.repo.pending(org_id=org_id, entity_type=entity_type, entity_id=entity_id).filter(approval_level=level).first()
        if not row:
            raise CorporateValidationError("Pending approval not found")
        if row.status != ApprovalRequest.STATUS_PENDING:
            raise CorporateValidationError("Approval history immutable after decision")
        if row.approver_id != approver.id:
            raise CorporateValidationError("Only assigned approver can decide")
        if (not allow_self_approve) and requester_id and requester_id == approver.id:
            raise CorporateValidationError("Requester cannot self-approve")
        if decision == "REJECT" and not comment.strip():
            raise CorporateValidationError("Rejection requires reason/comment")
        row.status = ApprovalRequest.STATUS_APPROVED if decision == "APPROVE" else ApprovalRequest.STATUS_REJECTED
        row.decision_comment = comment
        row.decided_at = timezone.now()
        row.save(update_fields=["status", "decision_comment", "decided_at", "updated_at"])
        ApprovalHistory.objects.create(
            org_id=org_id,
            entity_type=entity_type,
            entity_id=entity_id,
            approval_level=level,
            approver=approver,
            status=row.status,
            decision_comment=comment,
            decided_at=row.decided_at,
            request_ref=row,
        )
        return row


class SupplierService:
    def __init__(self, repository: SupplierRepository | None = None):
        self.repository = repository or SupplierRepository()

    def _validate(self, payload: dict) -> None:
        rating = payload.get("rating")
        if rating is not None and (rating < 1 or rating > 5):
            raise CorporateValidationError("rating must be between 1 and 5")

    @transaction.atomic
    def create(self, *, actor: User, payload: dict) -> Supplier:
        self._validate(payload)
        return self.repository.create(created_by=actor, updated_by=actor, **payload)

    def list(self, *, filters: SupplierFilters):
        return self.repository.list(filters)

    def get(self, *, org_id: int, supplier_id: int) -> Supplier:
        return self.repository.get_for_org(org_id=org_id, supplier_id=supplier_id)

    @transaction.atomic
    def update(self, *, supplier: Supplier, actor: User, payload: dict) -> Supplier:
        self._validate(payload)
        for k, v in payload.items():
            setattr(supplier, k, v)
        supplier.updated_by = actor
        supplier.save()
        return supplier


class ContractService:
    def __init__(self, repository: ContractRepository | None = None):
        self.repository = repository or ContractRepository()

    def _validate(self, payload: dict) -> None:
        eff = payload.get("effective_date")
        exp = payload.get("expiry_date")
        ren = payload.get("renewal_due_at")
        val = payload.get("contract_value")
        if eff and exp and exp <= eff:
            raise CorporateValidationError("expiry_date must be after effective_date")
        if ren and exp and ren > exp:
            raise CorporateValidationError("renewal_due_at must be <= expiry_date")
        if val is not None and Decimal(str(val)) < 0:
            raise CorporateValidationError("contract_value must be non-negative")

    @transaction.atomic
    def create(self, *, actor: User, payload: dict) -> CorporateContract:
        supplier = Supplier.objects.filter(id=payload["supplier_id"], org_id=payload["org_id"]).first()
        if not supplier:
            raise CorporateValidationError("Supplier not found")
        if supplier.status == Supplier.STATUS_BLACKLISTED:
            raise CorporateValidationError("Blacklisted supplier cannot be used in contracts")
        self._validate(payload)
        return self.repository.create(created_by=actor, updated_by=actor, supplier=supplier, owner_id=payload.get("owner_id"), **{k: v for k, v in payload.items() if k not in {"supplier_id", "owner_id"}})

    def list(self, *, filters: ContractFilters):
        return self.repository.list(filters)

    def get(self, *, org_id: int, contract_id: int):
        return self.repository.get_for_org(org_id=org_id, contract_id=contract_id)

    @transaction.atomic
    def update(self, *, contract: CorporateContract, actor: User, payload: dict) -> CorporateContract:
        self._validate(payload)
        if "supplier_id" in payload:
            supplier = Supplier.objects.filter(id=payload["supplier_id"], org_id=contract.org_id).first()
            if not supplier:
                raise CorporateValidationError("Supplier not found")
            if supplier.status == Supplier.STATUS_BLACKLISTED:
                raise CorporateValidationError("Blacklisted supplier cannot be used in contracts")
            contract.supplier = supplier
        for k, v in payload.items():
            if k != "supplier_id":
                setattr(contract, k, v)
        contract.updated_by = actor
        contract.save()
        return contract


class PurchaseOrderService:
    TERMINAL_STATUSES = {
        PurchaseOrder.STATUS_APPROVED,
        PurchaseOrder.STATUS_ORDERED,
        PurchaseOrder.STATUS_PARTIALLY_RECEIVED,
        PurchaseOrder.STATUS_RECEIVED,
        PurchaseOrder.STATUS_CANCELLED,
        PurchaseOrder.STATUS_VOID,
    }

    def __init__(
        self,
        repository: PurchaseOrderRepository | None = None,
        line_repository: PurchaseOrderLineItemRepository | None = None,
        calculator: PurchaseOrderCalculator | None = None,
        approvals: ApprovalWorkflowService | None = None,
    ):
        self.repository = repository or PurchaseOrderRepository()
        self.line_repository = line_repository or PurchaseOrderLineItemRepository()
        self.calculator = calculator or PurchaseOrderCalculator()
        self.approvals = approvals or ApprovalWorkflowService()

    def _refresh_totals(self, po: PurchaseOrder, line_items: list[dict]) -> None:
        totals = self.calculator.totals(line_items)
        po.subtotal = totals["subtotal"]
        po.tax_amount = totals["tax_amount"]
        po.discount_amount = totals["discount_amount"]
        po.total_amount = totals["total_amount"]

    @transaction.atomic
    def create(self, *, actor: User, payload: dict) -> PurchaseOrder:
        supplier = Supplier.objects.filter(id=payload["supplier_id"], org_id=payload["org_id"]).first()
        if not supplier:
            raise CorporateValidationError("Supplier not found")
        if supplier.status == Supplier.STATUS_BLACKLISTED:
            raise CorporateValidationError("Blacklisted supplier cannot be used in purchase orders")
        po = self.repository.create(
            org_id=payload["org_id"],
            po_number=payload["po_number"],
            supplier=supplier,
            contract_id=payload.get("contract_id"),
            property_id=payload.get("property_id"),
            department_id=payload.get("department_id"),
            requester_id=payload["requester_id"],
            approver_id=payload.get("approver_id"),
            secondary_approver_id=payload.get("secondary_approver_id"),
            status=payload.get("status", PurchaseOrder.STATUS_DRAFT),
            priority=payload.get("priority", PurchaseOrder.PRIORITY_MEDIUM),
            requested_date=payload.get("requested_date"),
            required_by=payload.get("required_by"),
            currency=payload.get("currency", "USD"),
            notes=payload.get("notes", ""),
            created_by=actor,
            updated_by=actor,
        )
        line_items = payload.get("line_items", [])
        self.line_repository.replace(po=po, line_items=line_items, calculator=self.calculator)
        self._refresh_totals(po, line_items)
        po.save()
        return po

    def get(self, *, org_id: int, po_id: int) -> PurchaseOrder:
        return self.repository.get_for_org(org_id=org_id, po_id=po_id)

    def list(self, *, filters: POFilters):
        return self.repository.list(filters)

    @transaction.atomic
    def update(self, *, po: PurchaseOrder, actor: User, payload: dict, admin_override: bool = False) -> PurchaseOrder:
        if po.status in self.TERMINAL_STATUSES and not admin_override:
            raise CorporateValidationError("Terminal PO cannot be modified")
        for f in ["priority", "required_by", "notes", "currency"]:
            if f in payload:
                setattr(po, f, payload[f])
        if "line_items" in payload:
            self.line_repository.replace(po=po, line_items=payload["line_items"], calculator=self.calculator)
            self._refresh_totals(po, payload["line_items"])
        po.updated_by = actor
        po.save()
        return po

    @transaction.atomic
    def submit(self, *, po: PurchaseOrder, actor: User) -> tuple[PurchaseOrder, list[ApprovalRequest]]:
        po.status = PurchaseOrder.STATUS_SUBMITTED
        po.updated_by = actor
        po.save(update_fields=["status", "updated_by", "updated_at"])
        levels = self.approvals.approval_levels_for_po(po.total_amount)
        if not levels:
            po.status = PurchaseOrder.STATUS_APPROVED
            po.approved_at = timezone.now()
            po.approver = actor
            po.save(update_fields=["status", "approved_at", "approver", "updated_at"])
            return po, []
        approvers_by_level: dict[int, User] = {}
        if 1 in levels:
            if not po.approver_id:
                raise CorporateValidationError("approver_id required for approval workflow")
            approvers_by_level[1] = po.approver
        if 2 in levels:
            if not po.secondary_approver_id:
                raise CorporateValidationError("secondary_approver_id required for high-value approval workflow")
            approvers_by_level[2] = po.secondary_approver
        reqs = self.approvals.create_approval_requests(
            org_id=po.org_id,
            entity_type=ApprovalRequest.ENTITY_PURCHASE_ORDER,
            entity_id=po.id,
            levels=levels,
            approvers_by_level=approvers_by_level,
        )
        return po, reqs

    @transaction.atomic
    def approve(self, *, po: PurchaseOrder, actor: User, comment: str = "") -> PurchaseOrder:
        if not po.line_items.exists():
            raise CorporateValidationError("Cannot approve empty PO")
        levels = self.approvals.approval_levels_for_po(po.total_amount)
        if levels:
            self.approvals.decide(
                org_id=po.org_id,
                entity_type=ApprovalRequest.ENTITY_PURCHASE_ORDER,
                entity_id=po.id,
                level=max(levels),
                approver=actor,
                decision="APPROVE",
                comment=comment,
                requester_id=po.requester_id,
            )
        po.status = PurchaseOrder.STATUS_APPROVED
        po.approved_at = timezone.now()
        po.approver = actor
        po.save(update_fields=["status", "approved_at", "approver", "updated_at"])
        return po

    @transaction.atomic
    def reject(self, *, po: PurchaseOrder, actor: User, reason: str) -> PurchaseOrder:
        if not reason.strip():
            raise CorporateValidationError("Rejection requires reason/comment")
        levels = self.approvals.approval_levels_for_po(po.total_amount)
        if levels:
            self.approvals.decide(
                org_id=po.org_id,
                entity_type=ApprovalRequest.ENTITY_PURCHASE_ORDER,
                entity_id=po.id,
                level=max(levels),
                approver=actor,
                decision="REJECT",
                comment=reason,
                requester_id=po.requester_id,
            )
        po.status = PurchaseOrder.STATUS_REJECTED
        po.approver = actor
        po.save(update_fields=["status", "approver", "updated_at"])
        return po


class CAPEXService:
    TERMINAL_STATUSES = {
        CAPEXRequest.STATUS_APPROVED,
        CAPEXRequest.STATUS_COMPLETED,
        CAPEXRequest.STATUS_CANCELLED,
        CAPEXRequest.STATUS_VOID,
    }

    HIGH_VALUE_THRESHOLD = Decimal("5000.00")

    def __init__(self, repository: CAPEXRepository | None = None, approvals: ApprovalWorkflowService | None = None):
        self.repository = repository or CAPEXRepository()
        self.approvals = approvals or ApprovalWorkflowService()

    def _validate(self, payload: dict, *, on_submit: bool = False) -> None:
        estimated = payload.get("estimated_amount")
        approved = payload.get("approved_amount")
        if estimated is not None and Decimal(str(estimated)) <= 0:
            raise CorporateValidationError("estimated_amount must be positive")
        if approved is not None and Decimal(str(approved)) < 0:
            raise CorporateValidationError("approved_amount must be non-negative")
        if estimated is not None and approved is not None and Decimal(str(approved)) > Decimal(str(estimated)):
            raise CorporateValidationError("approved_amount cannot exceed estimated_amount")
        if on_submit and not payload.get("justification", "").strip():
            raise CorporateValidationError("justification required before submission")
        if estimated is not None and Decimal(str(estimated)) > self.HIGH_VALUE_THRESHOLD and on_submit:
            if not payload.get("business_impact", "").strip():
                raise CorporateValidationError("business_impact required for high-value CAPEX")

    @transaction.atomic
    def create(self, *, actor: User, payload: dict) -> CAPEXRequest:
        self._validate(payload)
        return self.repository.create(created_by=actor, updated_by=actor, **payload)

    def get(self, *, org_id: int, capex_id: int) -> CAPEXRequest:
        return self.repository.get_for_org(org_id=org_id, capex_id=capex_id)

    def list(self, *, filters: CAPEXFilters):
        return self.repository.list(filters)

    @transaction.atomic
    def update(self, *, capex: CAPEXRequest, actor: User, payload: dict, admin_override: bool = False) -> CAPEXRequest:
        if capex.status in self.TERMINAL_STATUSES and not admin_override:
            raise CorporateValidationError("Terminal CAPEX cannot be modified")
        merged = {"estimated_amount": capex.estimated_amount, "approved_amount": capex.approved_amount, **payload}
        self._validate(merged)
        for k, v in payload.items():
            setattr(capex, k, v)
        capex.updated_by = actor
        capex.save()
        return capex

    @transaction.atomic
    def submit(self, *, capex: CAPEXRequest, actor: User) -> tuple[CAPEXRequest, list[ApprovalRequest]]:
        self._validate(
            {
                "estimated_amount": capex.estimated_amount,
                "approved_amount": capex.approved_amount,
                "justification": capex.justification,
                "business_impact": capex.business_impact,
            },
            on_submit=True,
        )
        capex.status = CAPEXRequest.STATUS_SUBMITTED
        capex.requested_at = timezone.now()
        capex.updated_by = actor
        capex.save(update_fields=["status", "requested_at", "updated_by", "updated_at"])
        levels = self.approvals.approval_levels_for_capex(capex.estimated_amount)
        approvers_by_level: dict[int, User] = {}
        if 1 in levels:
            if not capex.approver_id:
                raise CorporateValidationError("approver_id required for approval workflow")
            approvers_by_level[1] = capex.approver
        if 2 in levels:
            if not capex.secondary_approver_id:
                raise CorporateValidationError("secondary_approver_id required for high-value approval workflow")
            approvers_by_level[2] = capex.secondary_approver
        reqs = self.approvals.create_approval_requests(
            org_id=capex.org_id,
            entity_type=ApprovalRequest.ENTITY_CAPEX_REQUEST,
            entity_id=capex.id,
            levels=levels,
            approvers_by_level=approvers_by_level,
        )
        return capex, reqs

    @transaction.atomic
    def approve(self, *, capex: CAPEXRequest, actor: User, comment: str = "") -> CAPEXRequest:
        levels = self.approvals.approval_levels_for_capex(capex.estimated_amount)
        self.approvals.decide(
            org_id=capex.org_id,
            entity_type=ApprovalRequest.ENTITY_CAPEX_REQUEST,
            entity_id=capex.id,
            level=max(levels),
            approver=actor,
            decision="APPROVE",
            comment=comment,
            requester_id=capex.requester_id,
        )
        capex.status = CAPEXRequest.STATUS_APPROVED
        capex.approved_at = timezone.now()
        capex.approver = actor
        capex.save(update_fields=["status", "approved_at", "approver", "updated_at"])
        return capex

    @transaction.atomic
    def reject(self, *, capex: CAPEXRequest, actor: User, reason: str) -> CAPEXRequest:
        if not reason.strip():
            raise CorporateValidationError("Rejection requires reason/comment")
        levels = self.approvals.approval_levels_for_capex(capex.estimated_amount)
        self.approvals.decide(
            org_id=capex.org_id,
            entity_type=ApprovalRequest.ENTITY_CAPEX_REQUEST,
            entity_id=capex.id,
            level=max(levels),
            approver=actor,
            decision="REJECT",
            comment=reason,
            requester_id=capex.requester_id,
        )
        capex.status = CAPEXRequest.STATUS_REJECTED
        capex.approver = actor
        capex.save(update_fields=["status", "approver", "updated_at"])
        return capex
