from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.services.audit_logging import AuditContext
from application.services.corporate import (
    CAPEXFilters,
    CAPEXService,
    ContractFilters,
    ContractService,
    CorporateNotFoundError,
    CorporateValidationError,
    POFilters,
    PurchaseOrderService,
    SupplierFilters,
    SupplierService,
)
from infrastructure.db.core.models import CAPEXRequest, CorporateContract, PurchaseOrder, RolePermission, Supplier, UserRole
from infrastructure.services.audit_logging import get_audit_logger
from interfaces.api.serializers import (
    CAPEXCreateSerializer,
    CAPEXUpdateSerializer,
    ContractCreateSerializer,
    ContractUpdateSerializer,
    DecisionSerializer,
    PurchaseOrderCreateSerializer,
    PurchaseOrderUpdateSerializer,
    SupplierCreateSerializer,
    SupplierUpdateSerializer,
)



def _has_permission(user, code: str) -> bool:
    if not user:
        return False
    if hasattr(user, "is_authenticated") and not user.is_authenticated:
        return False
    if UserRole.objects.filter(user=user, role__name__iexact="super admin").exists():
        return True
    return RolePermission.objects.filter(role__user_roles__user=user, permission__code=code).exists()



def _audit_context(request, *, org_id: int, actor=None, property_id=None):
    meta = getattr(request, "audit_context", {})
    return AuditContext(
        org_id=org_id,
        property_id=property_id,
        actor_user_id=getattr(actor, "id", None),
        ip_address=meta.get("ip_address", request.META.get("REMOTE_ADDR", "")),
        user_agent=meta.get("user_agent", request.META.get("HTTP_USER_AGENT", "")),
    )



def _audit(request, *, org_id: int, action: str, target_type: str, target_id: str, metadata=None, actor=None, property_id=None):
    try:
        get_audit_logger().log_action(
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            metadata=metadata or {},
            context=_audit_context(request, org_id=org_id, actor=actor, property_id=property_id),
        )
    except Exception:
        pass



def _supplier_dict(s: Supplier):
    return {
        "id": s.id,
        "org_id": s.org_id,
        "supplier_code": s.supplier_code,
        "name": s.name,
        "contact_person": s.contact_person,
        "email": s.email,
        "phone": s.phone,
        "address": s.address,
        "tax_id": s.tax_id,
        "category": s.category,
        "status": s.status,
        "rating": s.rating,
        "notes": s.notes,
        "created_by": s.created_by_id,
        "updated_by": s.updated_by_id,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
    }



def _contract_dict(c: CorporateContract):
    return {
        "id": c.id,
        "org_id": c.org_id,
        "contract_code": c.contract_code,
        "supplier_id": c.supplier_id,
        "title": c.title,
        "description": c.description,
        "contract_type": c.contract_type,
        "status": c.status,
        "effective_date": c.effective_date,
        "expiry_date": c.expiry_date,
        "renewal_due_at": c.renewal_due_at,
        "contract_value": c.contract_value,
        "currency": c.currency,
        "attachment_id": c.attachment_id,
        "owner_id": c.owner_id,
        "created_by": c.created_by_id,
        "updated_by": c.updated_by_id,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }



def _po_dict(po: PurchaseOrder):
    return {
        "id": po.id,
        "org_id": po.org_id,
        "po_number": po.po_number,
        "supplier_id": po.supplier_id,
        "contract_id": po.contract_id,
        "property_id": po.property_id,
        "department_id": po.department_id,
        "requester_id": po.requester_id,
        "approver_id": po.approver_id,
        "secondary_approver_id": po.secondary_approver_id,
        "status": po.status,
        "priority": po.priority,
        "requested_date": po.requested_date,
        "required_by": po.required_by,
        "approved_at": po.approved_at,
        "ordered_at": po.ordered_at,
        "received_at": po.received_at,
        "subtotal": po.subtotal,
        "tax_amount": po.tax_amount,
        "discount_amount": po.discount_amount,
        "total_amount": po.total_amount,
        "currency": po.currency,
        "notes": po.notes,
        "line_items": [
            {
                "id": li.id,
                "item_name": li.item_name,
                "description": li.description,
                "quantity": li.quantity,
                "unit_price": li.unit_price,
                "tax_rate": li.tax_rate,
                "discount_amount": li.discount_amount,
                "line_total": li.line_total,
            }
            for li in po.line_items.order_by("id")
        ],
    }



def _capex_dict(c: CAPEXRequest):
    return {
        "id": c.id,
        "org_id": c.org_id,
        "capex_number": c.capex_number,
        "title": c.title,
        "description": c.description,
        "property_id": c.property_id,
        "department_id": c.department_id,
        "requester_id": c.requester_id,
        "approver_id": c.approver_id,
        "secondary_approver_id": c.secondary_approver_id,
        "category": c.category,
        "status": c.status,
        "estimated_amount": c.estimated_amount,
        "approved_amount": c.approved_amount,
        "currency": c.currency,
        "justification": c.justification,
        "business_impact": c.business_impact,
        "requested_at": c.requested_at,
        "approved_at": c.approved_at,
        "completed_at": c.completed_at,
    }


class SupplierListCreateView(APIView):
    service = SupplierService()

    def post(self, request):
        if not _has_permission(request.user, "corporate.suppliers.manage"):
            return Response({"detail": "Permission required: corporate.suppliers.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = SupplierCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            s = self.service.create(actor=request.user, payload=data)
        except (CorporateValidationError, IntegrityError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=s.org_id, action="supplier_created", target_type="supplier", target_id=s.id, actor=request.user)
        if s.status == Supplier.STATUS_BLACKLISTED:
            _audit(request, org_id=s.org_id, action="supplier_blacklisted", target_type="supplier", target_id=s.id, actor=request.user)
        return Response(_supplier_dict(s), status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "corporate.suppliers.view"):
            return Response({"detail": "Permission required: corporate.suppliers.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        rows = self.service.list(
            filters=SupplierFilters(
                org_id=org_id,
                category=request.query_params.get("category"),
                status=request.query_params.get("status"),
                rating=int(request.query_params["rating"]) if request.query_params.get("rating") else None,
                q=request.query_params.get("q"),
            )
        )
        return Response({"count": rows.count(), "results": [_supplier_dict(x) for x in rows.order_by("-created_at")]})


class SupplierDetailView(APIView):
    service = SupplierService()

    def get(self, request, id: int):
        if not _has_permission(request.user, "corporate.suppliers.view"):
            return Response({"detail": "Permission required: corporate.suppliers.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            row = self.service.get(org_id=org_id, supplier_id=id)
        except CorporateNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(_supplier_dict(row))

    def patch(self, request, id: int):
        if not _has_permission(request.user, "corporate.suppliers.manage"):
            return Response({"detail": "Permission required: corporate.suppliers.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        serializer = SupplierUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            row = self.service.get(org_id=org_id, supplier_id=id)
            updated = self.service.update(supplier=row, actor=request.user, payload=serializer.validated_data)
        except (CorporateValidationError, CorporateNotFoundError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=updated.org_id, action="supplier_updated", target_type="supplier", target_id=updated.id, actor=request.user)
        if updated.status == Supplier.STATUS_BLACKLISTED:
            _audit(request, org_id=updated.org_id, action="supplier_blacklisted", target_type="supplier", target_id=updated.id, actor=request.user)
        return Response(_supplier_dict(updated))


class ContractListCreateView(APIView):
    service = ContractService()

    def post(self, request):
        if not _has_permission(request.user, "corporate.contracts.manage"):
            return Response({"detail": "Permission required: corporate.contracts.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ContractCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            row = self.service.create(actor=request.user, payload=serializer.validated_data)
        except (CorporateValidationError, IntegrityError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=row.org_id, action="contract_created", target_type="contract", target_id=row.id, actor=request.user)
        if row.renewal_due_at:
            _audit(request, org_id=row.org_id, action="contract_renewal_due", target_type="contract", target_id=row.id, actor=request.user)
        return Response(_contract_dict(row), status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "corporate.contracts.view"):
            return Response({"detail": "Permission required: corporate.contracts.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        rows = self.service.list(
            filters=ContractFilters(
                org_id=org_id,
                supplier_id=int(request.query_params["supplier_id"]) if request.query_params.get("supplier_id") else None,
                status=request.query_params.get("status"),
                contract_type=request.query_params.get("contract_type"),
                owner_id=int(request.query_params["owner_id"]) if request.query_params.get("owner_id") else None,
                expiry_from=request.query_params.get("expiry_from"),
                expiry_to=request.query_params.get("expiry_to"),
            )
        )
        return Response({"count": rows.count(), "results": [_contract_dict(x) for x in rows.order_by("-created_at")]})


class ContractDetailView(APIView):
    service = ContractService()

    def get(self, request, id: int):
        if not _has_permission(request.user, "corporate.contracts.view"):
            return Response({"detail": "Permission required: corporate.contracts.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            row = self.service.get(org_id=org_id, contract_id=id)
        except CorporateNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(_contract_dict(row))

    def patch(self, request, id: int):
        if not _has_permission(request.user, "corporate.contracts.manage"):
            return Response({"detail": "Permission required: corporate.contracts.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        serializer = ContractUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            row = self.service.get(org_id=org_id, contract_id=id)
            updated = self.service.update(contract=row, actor=request.user, payload=serializer.validated_data)
        except (CorporateValidationError, CorporateNotFoundError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=updated.org_id, action="contract_updated", target_type="contract", target_id=updated.id, actor=request.user)
        return Response(_contract_dict(updated))


class PurchaseOrderListCreateView(APIView):
    service = PurchaseOrderService()

    def post(self, request):
        if not _has_permission(request.user, "corporate.purchase_orders.manage"):
            return Response({"detail": "Permission required: corporate.purchase_orders.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = PurchaseOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            row = self.service.create(actor=request.user, payload=serializer.validated_data)
        except (CorporateValidationError, IntegrityError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=row.org_id, action="purchase_order_created", target_type="purchase_order", target_id=row.id, actor=request.user, property_id=row.property_id)
        return Response(_po_dict(row), status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "corporate.purchase_orders.view"):
            return Response({"detail": "Permission required: corporate.purchase_orders.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        rows = self.service.list(
            filters=POFilters(
                org_id=org_id,
                status=request.query_params.get("status"),
                supplier_id=int(request.query_params["supplier_id"]) if request.query_params.get("supplier_id") else None,
            )
        )
        return Response({"count": rows.count(), "results": [_po_dict(x) for x in rows.order_by("-created_at")]})


class PurchaseOrderDetailView(APIView):
    service = PurchaseOrderService()

    def get(self, request, id: int):
        if not _has_permission(request.user, "corporate.purchase_orders.view"):
            return Response({"detail": "Permission required: corporate.purchase_orders.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            row = self.service.get(org_id=org_id, po_id=id)
        except CorporateNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(_po_dict(row))

    def patch(self, request, id: int):
        if not _has_permission(request.user, "corporate.purchase_orders.manage"):
            return Response({"detail": "Permission required: corporate.purchase_orders.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        serializer = PurchaseOrderUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            row = self.service.get(org_id=org_id, po_id=id)
            updated = self.service.update(
                po=row,
                actor=request.user,
                payload=serializer.validated_data,
                admin_override=serializer.validated_data.get("admin_override", False),
            )
        except (CorporateValidationError, CorporateNotFoundError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=updated.org_id, action="purchase_order_updated", target_type="purchase_order", target_id=updated.id, actor=request.user)
        return Response(_po_dict(updated))


class PurchaseOrderSubmitView(APIView):
    service = PurchaseOrderService()

    def post(self, request, id: int):
        if not _has_permission(request.user, "corporate.purchase_orders.manage"):
            return Response({"detail": "Permission required: corporate.purchase_orders.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        try:
            po = self.service.get(org_id=org_id, po_id=id)
            po, reqs = self.service.submit(po=po, actor=request.user)
        except (CorporateValidationError, CorporateNotFoundError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=po.org_id, action="purchase_order_submitted", target_type="purchase_order", target_id=po.id, actor=request.user)
        for req in reqs:
            _audit(request, org_id=po.org_id, action="approval_request_created", target_type="approval_request", target_id=req.id, actor=request.user)
        return Response(_po_dict(po))


class PurchaseOrderApproveView(APIView):
    service = PurchaseOrderService()

    def post(self, request, id: int):
        if not _has_permission(request.user, "corporate.purchase_orders.manage"):
            return Response({"detail": "Permission required: corporate.purchase_orders.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = DecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        try:
            po = self.service.get(org_id=org_id, po_id=id)
            po = self.service.approve(po=po, actor=request.user, comment=serializer.validated_data.get("comment", ""))
        except (CorporateValidationError, CorporateNotFoundError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=po.org_id, action="purchase_order_approved", target_type="purchase_order", target_id=po.id, actor=request.user)
        _audit(request, org_id=po.org_id, action="approval_decision_recorded", target_type="purchase_order", target_id=po.id, actor=request.user)
        return Response(_po_dict(po))


class PurchaseOrderRejectView(APIView):
    service = PurchaseOrderService()

    def post(self, request, id: int):
        if not _has_permission(request.user, "corporate.purchase_orders.manage"):
            return Response({"detail": "Permission required: corporate.purchase_orders.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = DecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        try:
            po = self.service.get(org_id=org_id, po_id=id)
            po = self.service.reject(po=po, actor=request.user, reason=serializer.validated_data.get("comment", ""))
        except (CorporateValidationError, CorporateNotFoundError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=po.org_id, action="purchase_order_rejected", target_type="purchase_order", target_id=po.id, actor=request.user)
        _audit(request, org_id=po.org_id, action="approval_decision_recorded", target_type="purchase_order", target_id=po.id, actor=request.user)
        return Response(_po_dict(po))


class PurchaseOrderStatusActionView(APIView):
    status_value = PurchaseOrder.STATUS_ORDERED
    action_name = "purchase_order_ordered"

    def post(self, request, id: int):
        if not _has_permission(request.user, "corporate.purchase_orders.manage"):
            return Response({"detail": "Permission required: corporate.purchase_orders.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        row = PurchaseOrder.objects.filter(id=id, org_id=org_id).first()
        if not row:
            return Response({"detail": "Purchase order not found"}, status=status.HTTP_404_NOT_FOUND)
        row.status = self.status_value
        if self.status_value == PurchaseOrder.STATUS_ORDERED:
            row.ordered_at = timezone.now()
        if self.status_value in [PurchaseOrder.STATUS_RECEIVED, PurchaseOrder.STATUS_PARTIALLY_RECEIVED]:
            row.received_at = timezone.now()
        row.updated_by = request.user
        row.save()
        _audit(request, org_id=row.org_id, action=self.action_name, target_type="purchase_order", target_id=row.id, actor=request.user)
        return Response(_po_dict(row))


class PurchaseOrderOrderedView(PurchaseOrderStatusActionView):
    status_value = PurchaseOrder.STATUS_ORDERED
    action_name = "purchase_order_ordered"


class PurchaseOrderReceiveView(PurchaseOrderStatusActionView):
    status_value = PurchaseOrder.STATUS_RECEIVED
    action_name = "purchase_order_received"


class PurchaseOrderCancelView(PurchaseOrderStatusActionView):
    status_value = PurchaseOrder.STATUS_CANCELLED
    action_name = "purchase_order_cancelled"


class PurchaseOrderVoidView(PurchaseOrderStatusActionView):
    status_value = PurchaseOrder.STATUS_VOID
    action_name = "purchase_order_voided"


class CAPEXListCreateView(APIView):
    service = CAPEXService()

    def post(self, request):
        if not _has_permission(request.user, "corporate.capex.manage"):
            return Response({"detail": "Permission required: corporate.capex.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = CAPEXCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            row = self.service.create(actor=request.user, payload=serializer.validated_data)
        except (CorporateValidationError, IntegrityError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=row.org_id, action="capex_created", target_type="capex_request", target_id=row.id, actor=request.user)
        return Response(_capex_dict(row), status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "corporate.capex.view"):
            return Response({"detail": "Permission required: corporate.capex.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        rows = self.service.list(filters=CAPEXFilters(org_id=org_id, status=request.query_params.get("status"), category=request.query_params.get("category")))
        return Response({"count": rows.count(), "results": [_capex_dict(x) for x in rows.order_by("-created_at")]})


class CAPEXDetailView(APIView):
    service = CAPEXService()

    def get(self, request, id: int):
        if not _has_permission(request.user, "corporate.capex.view"):
            return Response({"detail": "Permission required: corporate.capex.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            row = self.service.get(org_id=org_id, capex_id=id)
        except CorporateNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(_capex_dict(row))

    def patch(self, request, id: int):
        if not _has_permission(request.user, "corporate.capex.manage"):
            return Response({"detail": "Permission required: corporate.capex.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = CAPEXUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        try:
            row = self.service.get(org_id=org_id, capex_id=id)
            updated = self.service.update(
                capex=row,
                actor=request.user,
                payload=serializer.validated_data,
                admin_override=serializer.validated_data.get("admin_override", False),
            )
        except (CorporateValidationError, CorporateNotFoundError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=updated.org_id, action="capex_updated", target_type="capex_request", target_id=updated.id, actor=request.user)
        return Response(_capex_dict(updated))


class CAPEXSubmitView(APIView):
    service = CAPEXService()

    def post(self, request, id: int):
        if not _has_permission(request.user, "corporate.capex.manage"):
            return Response({"detail": "Permission required: corporate.capex.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        try:
            row = self.service.get(org_id=org_id, capex_id=id)
            row, reqs = self.service.submit(capex=row, actor=request.user)
        except (CorporateValidationError, CorporateNotFoundError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=row.org_id, action="capex_submitted", target_type="capex_request", target_id=row.id, actor=request.user)
        for req in reqs:
            _audit(request, org_id=row.org_id, action="approval_request_created", target_type="approval_request", target_id=req.id, actor=request.user)
        return Response(_capex_dict(row))


class CAPEXReviewView(APIView):
    def post(self, request, id: int):
        if not _has_permission(request.user, "corporate.capex.manage"):
            return Response({"detail": "Permission required: corporate.capex.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        row = CAPEXRequest.objects.filter(id=id, org_id=org_id).first()
        if not row:
            return Response({"detail": "CAPEX request not found"}, status=status.HTTP_404_NOT_FOUND)
        row.status = CAPEXRequest.STATUS_UNDER_REVIEW
        row.save(update_fields=["status", "updated_at"])
        _audit(request, org_id=row.org_id, action="capex_under_review", target_type="capex_request", target_id=row.id, actor=request.user)
        return Response(_capex_dict(row))


class CAPEXApproveView(APIView):
    service = CAPEXService()

    def post(self, request, id: int):
        if not _has_permission(request.user, "corporate.capex.manage"):
            return Response({"detail": "Permission required: corporate.capex.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = DecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        try:
            row = self.service.get(org_id=org_id, capex_id=id)
            row = self.service.approve(capex=row, actor=request.user, comment=serializer.validated_data.get("comment", ""))
        except (CorporateValidationError, CorporateNotFoundError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=row.org_id, action="capex_approved", target_type="capex_request", target_id=row.id, actor=request.user)
        _audit(request, org_id=row.org_id, action="approval_decision_recorded", target_type="capex_request", target_id=row.id, actor=request.user)
        return Response(_capex_dict(row))


class CAPEXRejectView(APIView):
    service = CAPEXService()

    def post(self, request, id: int):
        if not _has_permission(request.user, "corporate.capex.manage"):
            return Response({"detail": "Permission required: corporate.capex.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = DecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        try:
            row = self.service.get(org_id=org_id, capex_id=id)
            row = self.service.reject(capex=row, actor=request.user, reason=serializer.validated_data.get("comment", ""))
        except (CorporateValidationError, CorporateNotFoundError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=row.org_id, action="capex_rejected", target_type="capex_request", target_id=row.id, actor=request.user)
        _audit(request, org_id=row.org_id, action="approval_decision_recorded", target_type="capex_request", target_id=row.id, actor=request.user)
        return Response(_capex_dict(row))


class CAPEXStatusActionView(APIView):
    status_value = CAPEXRequest.STATUS_BUDGET_RELEASED
    action_name = "capex_budget_released"

    def post(self, request, id: int):
        if not _has_permission(request.user, "corporate.capex.manage"):
            return Response({"detail": "Permission required: corporate.capex.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        row = CAPEXRequest.objects.filter(id=id, org_id=org_id).first()
        if not row:
            return Response({"detail": "CAPEX request not found"}, status=status.HTTP_404_NOT_FOUND)
        row.status = self.status_value
        if self.status_value == CAPEXRequest.STATUS_COMPLETED:
            row.completed_at = timezone.now()
        row.save(update_fields=["status", "completed_at", "updated_at"])
        _audit(request, org_id=row.org_id, action=self.action_name, target_type="capex_request", target_id=row.id, actor=request.user)
        return Response(_capex_dict(row))


class CAPEXReleaseBudgetView(CAPEXStatusActionView):
    status_value = CAPEXRequest.STATUS_BUDGET_RELEASED
    action_name = "capex_budget_released"


class CAPEXCompleteView(CAPEXStatusActionView):
    status_value = CAPEXRequest.STATUS_COMPLETED
    action_name = "capex_completed"


class CAPEXCancelView(CAPEXStatusActionView):
    status_value = CAPEXRequest.STATUS_CANCELLED
    action_name = "capex_cancelled"


class CAPEXVoidView(CAPEXStatusActionView):
    status_value = CAPEXRequest.STATUS_VOID
    action_name = "capex_voided"
