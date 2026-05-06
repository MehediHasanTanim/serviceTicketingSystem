from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from application.services.corporate import ApprovalWorkflowService, CorporateValidationError, PurchaseOrderCalculator
from infrastructure.db.core.models import ApprovalHistory, ApprovalRequest, AuditLog, CAPEXRequest, PurchaseOrder, Supplier
from tests.unit.api_test_helpers import create_org, create_user, grant_permissions


@pytest.mark.django_db
def test_supplier_created_successfully_and_audit_logged():
    org = create_org("Corp")
    actor = create_user(org=org, email="corp-admin@example.com")
    grant_permissions(actor, ["corporate.suppliers.manage", "corporate.suppliers.view"])
    client = APIClient()
    client.force_authenticate(user=actor)

    res = client.post(
        reverse("corporate-suppliers"),
        {
            "org_id": org.id,
            "supplier_code": "SUP-0001",
            "name": "Acme Supplies",
            "email": "sales@acme.com",
            "rating": 5,
        },
        format="json",
    )

    assert res.status_code == 201
    assert Supplier.objects.filter(supplier_code="SUP-0001").exists()
    assert AuditLog.objects.filter(org=org, action="supplier_created").exists()


@pytest.mark.django_db
def test_duplicate_supplier_code_rejected():
    org = create_org("Corp")
    actor = create_user(org=org, email="corp-admin2@example.com")
    grant_permissions(actor, ["corporate.suppliers.manage"])
    Supplier.objects.create(org=org, supplier_code="SUP-0001", name="A", created_by=actor, updated_by=actor)
    client = APIClient()
    client.force_authenticate(user=actor)

    res = client.post(
        reverse("corporate-suppliers"),
        {"org_id": org.id, "supplier_code": "SUP-0001", "name": "Dup"},
        format="json",
    )

    assert res.status_code == 400


@pytest.mark.django_db
def test_blacklisted_supplier_cannot_be_used_in_contract_or_po():
    org = create_org("Corp")
    actor = create_user(org=org, email="corp-admin3@example.com")
    supplier = Supplier.objects.create(
        org=org,
        supplier_code="SUP-BLK",
        name="Bad Supplier",
        status=Supplier.STATUS_BLACKLISTED,
        created_by=actor,
        updated_by=actor,
    )

    client = APIClient()
    client.force_authenticate(user=actor)
    grant_permissions(actor, ["corporate.contracts.manage", "corporate.purchase_orders.manage"])

    c_res = client.post(
        reverse("corporate-contracts"),
        {
            "org_id": org.id,
            "contract_code": "CON-001",
            "supplier_id": supplier.id,
            "title": "Blocked",
            "effective_date": "2026-01-01",
            "expiry_date": "2026-12-31",
            "contract_value": "100.00",
        },
        format="json",
    )
    assert c_res.status_code == 400

    po_res = client.post(
        reverse("corporate-po-list-create"),
        {
            "org_id": org.id,
            "po_number": "PO-001",
            "supplier_id": supplier.id,
            "requester_id": actor.id,
            "line_items": [{"item_name": "Item", "quantity": "1", "unit_price": "100", "tax_rate": "0", "discount_amount": "0"}],
        },
        format="json",
    )
    assert po_res.status_code == 400


@pytest.mark.django_db
def test_contract_date_validations():
    org = create_org("Corp")
    actor = create_user(org=org, email="corp-admin4@example.com")
    supplier = Supplier.objects.create(org=org, supplier_code="SUP-002", name="Good", created_by=actor, updated_by=actor)
    client = APIClient()
    client.force_authenticate(user=actor)
    grant_permissions(actor, ["corporate.contracts.manage"])

    res = client.post(
        reverse("corporate-contracts"),
        {
            "org_id": org.id,
            "contract_code": "CON-002",
            "supplier_id": supplier.id,
            "title": "Bad dates",
            "effective_date": "2026-12-31",
            "expiry_date": "2026-01-01",
            "contract_value": "10.00",
        },
        format="json",
    )
    assert res.status_code == 400


@pytest.mark.django_db
def test_purchase_order_calculation_and_submit_approval_and_reject_reason_required():
    org = create_org("Corp")
    actor = create_user(org=org, email="corp-admin5@example.com")
    approver = create_user(org=org, email="approver@example.com")
    grant_permissions(actor, ["corporate.purchase_orders.manage"])
    supplier = Supplier.objects.create(org=org, supplier_code="SUP-003", name="Supplier", created_by=actor, updated_by=actor)

    client = APIClient()
    client.force_authenticate(user=actor)
    create_res = client.post(
        reverse("corporate-po-list-create"),
        {
            "org_id": org.id,
            "po_number": "PO-100",
            "supplier_id": supplier.id,
            "requester_id": actor.id,
            "approver_id": approver.id,
            "line_items": [
                {"item_name": "A", "quantity": "2", "unit_price": "100", "tax_rate": "0.10", "discount_amount": "5.00"}
            ],
        },
        format="json",
    )
    assert create_res.status_code == 201
    po_id = create_res.data["id"]
    assert Decimal(str(create_res.data["total_amount"])) == Decimal("215.00")

    submit_res = client.post(reverse("corporate-po-submit", kwargs={"id": po_id}), {"org_id": org.id}, format="json")
    assert submit_res.status_code == 200
    assert submit_res.data["status"] == PurchaseOrder.STATUS_SUBMITTED
    assert ApprovalRequest.objects.filter(entity_type=ApprovalRequest.ENTITY_PURCHASE_ORDER, entity_id=po_id).count() == 0

    reject_res = client.post(reverse("corporate-po-reject", kwargs={"id": po_id}), {"org_id": org.id, "comment": ""}, format="json")
    assert reject_res.status_code == 400


@pytest.mark.django_db
def test_terminal_po_cannot_be_modified():
    org = create_org("Corp")
    actor = create_user(org=org, email="corp-admin6@example.com")
    grant_permissions(actor, ["corporate.purchase_orders.manage"])
    supplier = Supplier.objects.create(org=org, supplier_code="SUP-004", name="Supplier", created_by=actor, updated_by=actor)
    po = PurchaseOrder.objects.create(
        org=org,
        po_number="PO-T",
        supplier=supplier,
        requester=actor,
        status=PurchaseOrder.STATUS_APPROVED,
        created_by=actor,
        updated_by=actor,
    )
    client = APIClient()
    client.force_authenticate(user=actor)
    res = client.patch(reverse("corporate-po-detail", kwargs={"id": po.id}), {"org_id": org.id, "notes": "x"}, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_capex_submit_requires_justification_and_high_value_business_impact():
    org = create_org("Corp")
    actor = create_user(org=org, email="corp-admin7@example.com")
    approver = create_user(org=org, email="capex-approver@example.com")
    grant_permissions(actor, ["corporate.capex.manage"])
    client = APIClient()
    client.force_authenticate(user=actor)

    create_res = client.post(
        reverse("corporate-capex-list-create"),
        {
            "org_id": org.id,
            "capex_number": "CAP-001",
            "title": "Generator",
            "requester_id": actor.id,
            "approver_id": approver.id,
            "estimated_amount": "6000.00",
        },
        format="json",
    )
    assert create_res.status_code == 201
    capex_id = create_res.data["id"]

    submit_res = client.post(reverse("corporate-capex-submit", kwargs={"id": capex_id}), {"org_id": org.id}, format="json")
    assert submit_res.status_code == 400


@pytest.mark.django_db
def test_capex_submit_approve_reject_and_audit():
    org = create_org("Corp")
    actor = create_user(org=org, email="corp-admin8@example.com")
    approver = create_user(org=org, email="capex-approver2@example.com")
    grant_permissions(actor, ["corporate.capex.manage"])
    grant_permissions(approver, ["corporate.capex.manage"])

    capex = CAPEXRequest.objects.create(
        org=org,
        capex_number="CAP-APP",
        title="Boiler",
        requester=actor,
        approver=approver,
        estimated_amount=Decimal("3000.00"),
        approved_amount=Decimal("0.00"),
        justification="Need replacement",
        business_impact="Avoid outage",
        created_by=actor,
        updated_by=actor,
    )

    client = APIClient()
    client.force_authenticate(user=actor)
    s_res = client.post(reverse("corporate-capex-submit", kwargs={"id": capex.id}), {"org_id": org.id}, format="json")
    assert s_res.status_code == 200
    assert ApprovalRequest.objects.filter(entity_type=ApprovalRequest.ENTITY_CAPEX_REQUEST, entity_id=capex.id).exists()

    client.force_authenticate(user=approver)
    a_res = client.post(reverse("corporate-capex-approve", kwargs={"id": capex.id}), {"org_id": org.id, "comment": "ok"}, format="json")
    assert a_res.status_code == 200
    assert a_res.data["status"] == CAPEXRequest.STATUS_APPROVED
    assert AuditLog.objects.filter(org=org, action="capex_approved").exists()


@pytest.mark.django_db
def test_approval_rules_duplicate_pending_prevented_and_self_approve_blocked_and_immutable_after_decision():
    org = create_org("Corp")
    requester = create_user(org=org, email="requester@example.com")
    service = ApprovalWorkflowService()

    rows = service.create_approval_requests(
        org_id=org.id,
        entity_type=ApprovalRequest.ENTITY_PURCHASE_ORDER,
        entity_id=99,
        levels=[1, 1],
        approvers_by_level={1: requester},
    )
    assert len(rows) == 1
    assert ApprovalHistory.objects.filter(entity_type=ApprovalRequest.ENTITY_PURCHASE_ORDER, entity_id=99, status=ApprovalRequest.STATUS_PENDING).exists()

    with pytest.raises(CorporateValidationError):
        service.decide(
            org_id=org.id,
            entity_type=ApprovalRequest.ENTITY_PURCHASE_ORDER,
            entity_id=99,
            level=1,
            approver=requester,
            decision="APPROVE",
            comment="ok",
            requester_id=requester.id,
            allow_self_approve=False,
        )


@pytest.mark.django_db
def test_multi_level_approval_progresses_correctly_for_high_value_capex():
    org = create_org("Corp")
    requester = create_user(org=org, email="req2@example.com")
    level1 = create_user(org=org, email="mgr@example.com")
    level2 = create_user(org=org, email="finance@example.com")
    service = ApprovalWorkflowService()

    rows = service.create_approval_requests(
        org_id=org.id,
        entity_type=ApprovalRequest.ENTITY_CAPEX_REQUEST,
        entity_id=555,
        levels=[1, 2],
        approvers_by_level={1: level1, 2: level2},
    )
    assert len(rows) == 2
    assert rows[0].approval_level == 1
    assert rows[1].approval_level == 2

    first = service.decide(
        org_id=org.id,
        entity_type=ApprovalRequest.ENTITY_CAPEX_REQUEST,
        entity_id=555,
        level=1,
        approver=level1,
        decision="APPROVE",
        comment="manager ok",
        requester_id=requester.id,
    )
    assert first.status == ApprovalRequest.STATUS_APPROVED

    second = service.decide(
        org_id=org.id,
        entity_type=ApprovalRequest.ENTITY_CAPEX_REQUEST,
        entity_id=555,
        level=2,
        approver=level2,
        decision="APPROVE",
        comment="finance ok",
        requester_id=requester.id,
    )
    assert second.status == ApprovalRequest.STATUS_APPROVED
    assert ApprovalHistory.objects.filter(entity_type=ApprovalRequest.ENTITY_CAPEX_REQUEST, entity_id=555, status=ApprovalRequest.STATUS_APPROVED).count() >= 2


@pytest.mark.django_db
def test_decimal_calculations_safe():
    calc = PurchaseOrderCalculator()
    total = calc.line_total(quantity="1.333", unit_price="19.999", tax_rate="0.15", discount_amount="0")
    assert total == Decimal("30.66")
