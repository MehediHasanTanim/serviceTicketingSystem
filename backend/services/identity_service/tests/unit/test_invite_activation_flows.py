from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken

from infrastructure.db.core.models import (
    InviteToken,
    Organization,
    Permission,
    Role,
    RolePermission,
    User,
    UserCredential,
    UserRole,
)
from interfaces.api.auth_views import _create_invite_token


def _create_org(org_id: int = 1) -> Organization:
    return Organization.objects.create(
        id=org_id,
        name=f"Org {org_id}",
        legal_name=f"Org {org_id} LLC",
    )


def _create_user(org: Organization, email: str, status_value: str = "active") -> User:
    return User.objects.create(
        org=org,
        email=email,
        display_name=email.split("@")[0].title(),
        status=status_value,
    )


def _grant_users_manage_permission(user: User) -> None:
    role = Role.objects.create(org=user.org, name="admin", description="")
    permission = Permission.objects.create(code="users.manage", description="")
    RolePermission.objects.create(role=role, permission=permission)
    UserRole.objects.create(user=user, role=role)


@pytest.mark.django_db
@pytest.mark.unit
def test_create_invite_token_creates_persisted_token_with_future_expiry():
    org = _create_org()
    user = _create_user(org, "invitee@example.com", status_value="invited")

    token = _create_invite_token(user)

    assert token.user_id == user.id
    assert len(token.token) == 64
    assert token.expires_at > timezone.now()
    assert InviteToken.objects.filter(id=token.id).exists()


@pytest.mark.django_db
@pytest.mark.unit
def test_user_invite_endpoint_creates_token_and_sends_email(settings):
    org = _create_org()
    actor = _create_user(org, "manager@example.com")
    target = _create_user(org, "staff@example.com", status_value="active")
    _grant_users_manage_permission(actor)

    access_token = str(JWTRefreshToken.for_user(actor).access_token)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    settings.EMAIL_HOST = "smtp.example.com"
    settings.DEFAULT_FROM_EMAIL = "noreply@example.com"
    with patch("interfaces.api.auth_views.send_mail", return_value=1) as send_mail_mock:
        response = client.post(reverse("user-invite", kwargs={"user_id": target.id}), {}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "invited"

    token = InviteToken.objects.filter(user=target).order_by("-created_at").first()
    assert token is not None
    assert token.sent_at is not None
    assert send_mail_mock.called


@pytest.mark.django_db
@pytest.mark.unit
def test_activate_invite_success_sets_password_marks_token_used_and_activates_user():
    org = _create_org()
    user = _create_user(org, "invited.user@example.com", status_value="invited")
    invite = InviteToken.objects.create(
        token="a" * 64,
        user=user,
        expires_at=timezone.now() + timedelta(hours=2),
    )
    client = APIClient()

    response = client.post(
        reverse("auth-activate"),
        {
            "token": invite.token,
            "password": "NewStrongPass1!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    invite.refresh_from_db()
    user.refresh_from_db()
    credential = UserCredential.objects.get(user=user)

    assert user.status == "active"
    assert invite.used_at is not None
    assert check_password("NewStrongPass1!", credential.password_hash)


@pytest.mark.django_db
@pytest.mark.unit
def test_activate_invite_returns_error_for_used_token():
    org = _create_org()
    user = _create_user(org, "used.token.user@example.com", status_value="invited")
    InviteToken.objects.create(
        token="b" * 64,
        user=user,
        expires_at=timezone.now() + timedelta(hours=2),
        used_at=timezone.now(),
    )
    client = APIClient()

    response = client.post(
        reverse("auth-activate"),
        {"token": "b" * 64, "password": "NewStrongPass1!"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["detail"] == "Invite token already used"


@pytest.mark.django_db
@pytest.mark.unit
def test_activate_invite_returns_error_for_expired_token():
    org = _create_org()
    user = _create_user(org, "expired.token.user@example.com", status_value="invited")
    InviteToken.objects.create(
        token="c" * 64,
        user=user,
        expires_at=timezone.now() - timedelta(minutes=1),
    )
    client = APIClient()

    response = client.post(
        reverse("auth-activate"),
        {"token": "c" * 64, "password": "NewStrongPass1!"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["detail"] == "Invite token expired"


@pytest.mark.django_db
@pytest.mark.unit
def test_activate_invite_returns_error_for_invalid_token():
    client = APIClient()

    response = client.post(
        reverse("auth-activate"),
        {"token": "d" * 64, "password": "NewStrongPass1!"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["detail"] == "Invalid invite token"
