import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.unit.api_test_helpers import authenticated_client, assign_role, create_org, create_user, grant_permissions


@pytest.mark.django_db
@pytest.mark.unit
def test_me_returns_user_profile_roles_and_permissions():
    org = create_org("Ops Org")
    user = create_user(org, email="me@example.com", display_name="Me User")
    assign_role(user, "admin")
    grant_permissions(user, ["users.view", "roles.manage"], role_name="ops-manager")

    client = authenticated_client(user)
    response = client.get(reverse("auth-me"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == user.id
    assert response.data["org_id"] == org.id
    assert response.data["email"] == "me@example.com"
    assert response.data["display_name"] == "Me User"
    assert sorted(response.data["roles"]) == ["admin", "ops-manager"]
    assert set(response.data["permissions"]) == {"users.view", "roles.manage"}
    assert response.data["is_admin"] is True
    assert response.data["is_super_admin"] is False


@pytest.mark.django_db
@pytest.mark.unit
def test_me_requires_authentication():
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.value")
    response = client.get(reverse("auth-me"))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
