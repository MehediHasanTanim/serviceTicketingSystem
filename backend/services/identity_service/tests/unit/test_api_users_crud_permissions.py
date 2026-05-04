import pytest
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from rest_framework import status

from infrastructure.db.core.models import User, UserCredential
from tests.unit.api_test_helpers import (
    assign_role,
    authenticated_client,
    create_org,
    create_user,
    grant_permissions,
)


@pytest.mark.django_db
@pytest.mark.unit
def test_users_list_requires_users_view_permission():
    org = create_org("Users Org")
    actor = create_user(org, email="actor@example.com")
    client = authenticated_client(actor)

    response = client.get(reverse("user-list-create"), {"org_id": org.id})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data["detail"] == "Permission required: users.view"


@pytest.mark.django_db
@pytest.mark.unit
def test_users_list_returns_results_when_authorized():
    org = create_org("Users Org")
    actor = create_user(org, email="viewer@example.com")
    grant_permissions(actor, ["users.view"], role_name="viewer")
    create_user(org, email="alice@example.com", display_name="Alice")
    create_user(org, email="bob@example.com", display_name="Bob")
    client = authenticated_client(actor)

    response = client.get(
        reverse("user-list-create"),
        {"org_id": org.id, "q": "ali", "page": 1, "page_size": 10},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["email"] == "alice@example.com"


@pytest.mark.django_db
@pytest.mark.unit
def test_users_list_applies_sorting_when_authorized():
    org = create_org("Users Org")
    actor = create_user(org, email="viewer@example.com")
    grant_permissions(actor, ["users.view"], role_name="viewer")
    create_user(org, email="sortcase.a@example.com", display_name="Alpha User")
    create_user(org, email="sortcase.c@example.com", display_name="Charlie User")
    create_user(org, email="sortcase.b@example.com", display_name="Bravo User")
    client = authenticated_client(actor)

    response = client.get(
        reverse("user-list-create"),
        {
            "org_id": org.id,
            "q": "sortcase.",
            "sort_by": "email",
            "sort_dir": "desc",
            "page": 1,
            "page_size": 10,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 3
    assert [user["email"] for user in response.data["results"]] == [
        "sortcase.c@example.com",
        "sortcase.b@example.com",
        "sortcase.a@example.com",
    ]


@pytest.mark.django_db
@pytest.mark.unit
def test_user_create_requires_users_manage_permission():
    org = create_org("Users Org")
    actor = create_user(org, email="actor@example.com")
    client = authenticated_client(actor)

    response = client.post(
        reverse("user-list-create"),
        {
            "org_id": org.id,
            "email": "new.user@example.com",
            "display_name": "New User",
            "status": "invited",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data["detail"] == "Permission required: users.manage"


@pytest.mark.django_db
@pytest.mark.unit
def test_user_create_with_active_status_requires_password():
    org = create_org("Users Org")
    actor = create_user(org, email="manager@example.com")
    grant_permissions(actor, ["users.manage"], role_name="manager")
    client = authenticated_client(actor)

    response = client.post(
        reverse("user-list-create"),
        {
            "org_id": org.id,
            "email": "active.user@example.com",
            "display_name": "Active User",
            "status": "active",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["detail"] == "Password is required for active users"


@pytest.mark.django_db
@pytest.mark.unit
def test_user_create_returns_conflict_for_duplicate_email():
    org = create_org("Users Org")
    actor = create_user(org, email="manager@example.com")
    grant_permissions(actor, ["users.manage"], role_name="manager")
    create_user(org, email="duplicate.user@example.com", display_name="Existing User")
    client = authenticated_client(actor)

    response = client.post(
        reverse("user-list-create"),
        {
            "org_id": org.id,
            "email": "Duplicate.User@example.com",
            "display_name": "New User",
            "status": "invited",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.data["detail"] == "User already exists"


@pytest.mark.django_db
@pytest.mark.unit
def test_user_create_and_update_and_delete_success_when_authorized():
    org = create_org("Users Org")
    actor = create_user(org, email="manager@example.com")
    grant_permissions(actor, ["users.manage"], role_name="manager")
    editor_role = assign_role(actor, "editor")
    client = authenticated_client(actor)

    create_response = client.post(
        reverse("user-list-create"),
        {
            "org_id": org.id,
            "email": "created.user@example.com",
            "display_name": "Created User",
            "status": "active",
            "password": "StrongPass1!",
            "role_name": editor_role.name,
        },
        format="json",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    created_user_id = create_response.data["id"]
    created_user = User.objects.get(id=created_user_id)
    assert created_user.status == "active"
    assert UserCredential.objects.filter(user=created_user).exists()

    patch_response = client.patch(
        reverse("user-detail", kwargs={"user_id": created_user_id}),
        {"display_name": "Updated User"},
        format="json",
    )
    assert patch_response.status_code == status.HTTP_200_OK
    assert patch_response.data["display_name"] == "Updated User"

    delete_response = client.delete(reverse("user-detail", kwargs={"user_id": created_user_id}))
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert not User.objects.filter(id=created_user_id).exists()


@pytest.mark.django_db
@pytest.mark.unit
def test_user_delete_super_admin_requires_requester_super_admin():
    org = create_org("Users Org")
    manager = create_user(org, email="manager@example.com")
    grant_permissions(manager, ["users.manage"], role_name="manager")

    super_target = create_user(org, email="super.target@example.com")
    assign_role(super_target, "super admin")
    UserCredential.objects.create(
        user=super_target,
        password_hash=make_password("StrongPass1!"),
        last_password_change_at=None,
    )

    client = authenticated_client(manager)
    response = client.delete(reverse("user-detail", kwargs={"user_id": super_target.id}))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data["detail"] == "Super admin required to delete this user"
