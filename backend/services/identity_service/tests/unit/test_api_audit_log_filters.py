from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from infrastructure.db.core.models import AuditLog
from tests.unit.api_test_helpers import authenticated_client, create_org, create_user, grant_permissions


def _create_log(
    *,
    org_id: int,
    actor_user_id: int,
    action: str,
    target_type: str,
    target_id: str,
    created_at,
):
    log = AuditLog.objects.create(
        org_id=org_id,
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_json={"note": action},
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    AuditLog.objects.filter(id=log.id).update(created_at=created_at)
    log.refresh_from_db()
    return log


@pytest.mark.django_db
@pytest.mark.unit
def test_audit_logs_requires_org_id_and_audit_view_permission():
    org = create_org("Audit Org")
    actor = create_user(org, email="audit.actor@example.com")
    client = authenticated_client(actor)

    missing_org_response = client.get(reverse("audit-logs"))
    forbidden_response = client.get(reverse("audit-logs"), {"org_id": org.id})

    assert missing_org_response.status_code == status.HTTP_400_BAD_REQUEST
    assert missing_org_response.data["detail"] == "org_id is required"
    assert forbidden_response.status_code == status.HTTP_403_FORBIDDEN
    assert forbidden_response.data["detail"] == "Permission required: audit.view"


@pytest.mark.django_db
@pytest.mark.unit
def test_audit_logs_filters_by_actor_action_target_and_date_range():
    org = create_org("Audit Org")
    actor = create_user(org, email="audit.viewer@example.com")
    other_actor = create_user(org, email="other.actor@example.com")
    grant_permissions(actor, ["audit.view"], role_name="auditor")
    client = authenticated_client(actor)

    now = timezone.now()
    match_log = _create_log(
        org_id=org.id,
        actor_user_id=actor.id,
        action="user.created",
        target_type="user",
        target_id="101",
        created_at=now - timedelta(days=1),
    )
    _create_log(
        org_id=org.id,
        actor_user_id=other_actor.id,
        action="role.updated",
        target_type="role",
        target_id="202",
        created_at=now - timedelta(days=10),
    )

    response = client.get(
        reverse("audit-logs"),
        {
            "org_id": org.id,
            "actor_user_id": actor.id,
            "action": "created",
            "target_type": "user",
            "target_id": "101",
            "date_from": (now - timedelta(days=2)).date().isoformat(),
            "date_to": now.date().isoformat(),
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == match_log.id
    assert response.data["results"][0]["action"] == "user.created"


@pytest.mark.django_db
@pytest.mark.unit
def test_audit_logs_applies_pagination_and_sorting():
    org = create_org("Audit Pagination Org")
    actor = create_user(org, email="audit.paging@example.com")
    grant_permissions(actor, ["audit.view"], role_name="auditor")
    client = authenticated_client(actor)

    now = timezone.now()
    _create_log(
        org_id=org.id,
        actor_user_id=actor.id,
        action="z.action",
        target_type="room",
        target_id="1",
        created_at=now - timedelta(days=3),
    )
    _create_log(
        org_id=org.id,
        actor_user_id=actor.id,
        action="m.action",
        target_type="building",
        target_id="2",
        created_at=now - timedelta(days=2),
    )
    _create_log(
        org_id=org.id,
        actor_user_id=actor.id,
        action="a.action",
        target_type="asset",
        target_id="3",
        created_at=now - timedelta(days=1),
    )

    created_sort_response = client.get(
        reverse("audit-logs"),
        {"org_id": org.id, "sort_by": "created_at", "sort_dir": "desc", "page": 1, "page_size": 2},
    )
    assert created_sort_response.status_code == status.HTTP_200_OK
    assert created_sort_response.data["count"] == 3
    assert len(created_sort_response.data["results"]) == 2
    assert created_sort_response.data["results"][0]["action"] == "a.action"
    assert created_sort_response.data["results"][1]["action"] == "m.action"

    page_two_response = client.get(
        reverse("audit-logs"),
        {"org_id": org.id, "sort_by": "created_at", "sort_dir": "desc", "page": 2, "page_size": 2},
    )
    assert page_two_response.status_code == status.HTTP_200_OK
    assert len(page_two_response.data["results"]) == 1
    assert page_two_response.data["results"][0]["action"] == "z.action"

    action_sort_response = client.get(
        reverse("audit-logs"),
        {"org_id": org.id, "sort_by": "action", "sort_dir": "asc", "page": 1, "page_size": 10},
    )
    assert action_sort_response.status_code == status.HTTP_200_OK
    assert [row["action"] for row in action_sort_response.data["results"]] == [
        "a.action",
        "m.action",
        "z.action",
    ]

    target_type_sort_response = client.get(
        reverse("audit-logs"),
        {"org_id": org.id, "sort_by": "target_type", "sort_dir": "asc", "page": 1, "page_size": 10},
    )
    assert target_type_sort_response.status_code == status.HTTP_200_OK
    assert [row["target_type"] for row in target_type_sort_response.data["results"]] == [
        "asset",
        "building",
        "room",
    ]
