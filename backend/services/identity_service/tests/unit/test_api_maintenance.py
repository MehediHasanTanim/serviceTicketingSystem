import pytest
from django.urls import reverse
from rest_framework import status

from infrastructure.db.core.models import Asset, AuditLog, MaintenanceTask
from tests.unit.api_test_helpers import authenticated_client, create_org, create_user, grant_permissions


@pytest.mark.django_db
@pytest.mark.unit
def test_asset_registry_and_filters_pagination_and_history_and_audit():
    org = create_org("Asset API Org")
    actor = create_user(org, email="asset-api@example.com")
    grant_permissions(actor, ["maintenance.assets.manage", "maintenance.assets.view", "audit.view"], role_name="manager")
    client = authenticated_client(actor)

    for i in range(3):
        res = client.post(
            reverse("maintenance-asset-list-create"),
            {
                "org_id": org.id,
                "name": f"Asset-{i}",
                "category": "HVAC" if i < 2 else "ELECTRICAL",
                "status": "ACTIVE",
                "criticality": "HIGH" if i == 0 else "MEDIUM",
            },
            format="json",
        )
        assert res.status_code == status.HTTP_201_CREATED

    list_res = client.get(reverse("maintenance-asset-list-create"), {"org_id": org.id, "category": "HVAC", "page": 1, "page_size": 1})
    assert list_res.status_code == status.HTTP_200_OK
    assert list_res.data["count"] == 2
    assert len(list_res.data["results"]) == 1

    asset_id = list_res.data["results"][0]["id"]
    status_res = client.post(
        reverse("maintenance-asset-status", kwargs={"asset_id": asset_id}),
        {"org_id": org.id, "new_status": "UNDER_MAINTENANCE", "reason": "routine"},
        format="json",
    )
    assert status_res.status_code == status.HTTP_200_OK

    history = client.get(reverse("maintenance-asset-history", kwargs={"asset_id": asset_id}), {"org_id": org.id})
    assert history.status_code == status.HTTP_200_OK
    assert history.data["count"] >= 2

    assert AuditLog.objects.filter(org=org, action="asset_status_changed").exists()


@pytest.mark.django_db
@pytest.mark.unit
def test_corrective_task_lifecycle_logbook_and_restricted_modification():
    org = create_org("Task API Org")
    actor = create_user(org, email="task-api@example.com")
    assignee = create_user(org, email="task-worker@example.com")
    grant_permissions(actor, ["maintenance.tasks.manage", "maintenance.tasks.view"], role_name="manager")
    client = authenticated_client(actor)

    asset = Asset.objects.create(
        org=org,
        asset_code="AST-API-1",
        name="Chiller",
        created_by=actor,
        updated_by=actor,
    )

    create = client.post(
        reverse("maintenance-task-list-create"),
        {"org_id": org.id, "task_type": "CORRECTIVE", "title": "Fix chiller", "asset_id": asset.id, "priority": "HIGH"},
        format="json",
    )
    assert create.status_code == status.HTTP_201_CREATED
    task_id = create.data["id"]

    assign = client.post(reverse("maintenance-task-assign", kwargs={"task_id": task_id}), {"org_id": org.id, "assignee_id": assignee.id}, format="json")
    assert assign.status_code == status.HTTP_200_OK

    start = client.post(reverse("maintenance-task-start", kwargs={"task_id": task_id}), {"org_id": org.id}, format="json")
    assert start.status_code == status.HTTP_200_OK

    complete_without_summary = client.post(reverse("maintenance-task-complete", kwargs={"task_id": task_id}), {"org_id": org.id}, format="json")
    assert complete_without_summary.status_code == status.HTTP_400_BAD_REQUEST

    logbook = client.post(
        reverse("maintenance-task-logbook", kwargs={"task_id": task_id}),
        {
            "org_id": org.id,
            "entry_type": "COMPLETION_SUMMARY",
            "description": "completed work",
            "labor": [{"technician_id": assignee.id, "hours": "2.00", "hourly_rate": "25.00"}],
        },
        format="json",
    )
    assert logbook.status_code == status.HTTP_201_CREATED

    complete = client.post(reverse("maintenance-task-complete", kwargs={"task_id": task_id}), {"org_id": org.id}, format="json")
    assert complete.status_code == status.HTTP_200_OK

    patch_after_complete = client.patch(reverse("maintenance-task-detail", kwargs={"task_id": task_id}), {"org_id": org.id, "title": "changed"}, format="json")
    assert patch_after_complete.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.unit
def test_qr_lookup_and_task_creation_flow_and_audit():
    org = create_org("QR API Org")
    actor = create_user(org, email="qr-api@example.com")
    grant_permissions(actor, ["maintenance.assets.manage", "maintenance.assets.view", "maintenance.tasks.manage", "maintenance.tasks.view"], role_name="manager")
    client = authenticated_client(actor)

    asset = Asset.objects.create(
        org=org,
        asset_code="AST-QR-1",
        qr_code="QR-001",
        name="Boiler",
        created_by=actor,
        updated_by=actor,
    )

    lookup = client.get(reverse("maintenance-asset-qr-lookup", kwargs={"qr_code": "QR-001"}), {"org_id": org.id})
    assert lookup.status_code == status.HTTP_200_OK
    assert lookup.data["asset"]["id"] == asset.id

    missing = client.get(reverse("maintenance-asset-qr-lookup", kwargs={"qr_code": "NOPE"}), {"org_id": org.id})
    assert missing.status_code == status.HTTP_404_NOT_FOUND

    create_from_qr = client.post(
        reverse("maintenance-asset-qr-task-create", kwargs={"qr_code": "QR-001"}),
        {"org_id": org.id, "task_type": "CORRECTIVE", "title": "Leaking valve", "priority": "URGENT"},
        format="json",
    )
    assert create_from_qr.status_code == status.HTTP_201_CREATED
    assert create_from_qr.data["asset_id"] == asset.id

    assert MaintenanceTask.objects.filter(org=org, asset=asset).exists()
    assert AuditLog.objects.filter(org=org, action="asset_qr_lookup").exists()


@pytest.mark.django_db
@pytest.mark.unit
def test_pm_scheduler_endpoint_creates_tasks():
    org = create_org("PM API Org")
    actor = create_user(org, email="pm-api@example.com")
    grant_permissions(actor, ["maintenance.pm.manage", "maintenance.tasks.view"], role_name="manager")
    client = authenticated_client(actor)

    from infrastructure.db.core.models import PMSchedule
    from django.utils import timezone
    from datetime import date, timedelta

    asset = Asset.objects.create(
        org=org,
        asset_code="AST-PM-1",
        name="Cooling Tower",
        created_by=actor,
        updated_by=actor,
    )
    PMSchedule.objects.create(
        asset=asset,
        title="PM tower",
        description="desc",
        frequency_type=PMSchedule.FREQ_DAILY,
        frequency_interval=1,
        next_run_at=timezone.now() - timedelta(minutes=1),
        start_date=date.today(),
        priority="MEDIUM",
        is_active=True,
        created_by=actor,
    )

    res = client.post(reverse("maintenance-pm-scheduler-run"), {"org_id": org.id}, format="json")
    assert res.status_code == status.HTTP_200_OK
    assert res.data["tasks_created"] == 1
