import pytest
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken

from infrastructure.db.core.models import Organization, RefreshToken, User, UserCredential


def _create_user_with_password(*, org_id: int = 1, email: str = "admin@example.com", password: str = "StrongPass1!"):
    org = Organization.objects.create(id=org_id, name=f"Org {org_id}", legal_name=f"Org {org_id} LLC")
    user = User.objects.create(
        org=org,
        email=email,
        display_name="Admin User",
        status="active",
    )
    UserCredential.objects.create(
        user=user,
        password_hash=make_password(password),
        last_password_change_at=timezone.now(),
    )
    return org, user, password


@pytest.mark.django_db
@pytest.mark.unit
def test_login_issues_jwt_pair_and_persists_refresh_record():
    org, _, password = _create_user_with_password()
    client = APIClient()

    response = client.post(
        reverse("auth-login"),
        {
            "org_id": org.id,
            "email": "admin@example.com",
            "password": password,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data
    assert response.data["access_expires_at"]
    assert response.data["refresh_expires_at"]

    refresh_token = JWTRefreshToken(response.data["refresh"])
    assert RefreshToken.objects.filter(key=refresh_token["jti"], revoked_at__isnull=True).exists()


@pytest.mark.django_db
@pytest.mark.unit
def test_login_rejects_invalid_credentials():
    org, _, _ = _create_user_with_password()
    client = APIClient()

    response = client.post(
        reverse("auth-login"),
        {
            "org_id": org.id,
            "email": "admin@example.com",
            "password": "WrongPassword!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["detail"] == "Invalid credentials"


@pytest.mark.django_db
@pytest.mark.unit
def test_refresh_rotates_token_and_revokes_previous_refresh_record():
    org, _, password = _create_user_with_password()
    client = APIClient()

    login_response = client.post(
        reverse("auth-login"),
        {
            "org_id": org.id,
            "email": "admin@example.com",
            "password": password,
        },
        format="json",
    )
    assert login_response.status_code == status.HTTP_200_OK
    original_refresh = login_response.data["refresh"]
    original_jti = JWTRefreshToken(original_refresh)["jti"]

    refresh_response = client.post(
        reverse("auth-refresh"),
        {"refresh_token": original_refresh},
        format="json",
    )

    assert refresh_response.status_code == status.HTTP_200_OK
    assert refresh_response.data["access"]
    assert refresh_response.data["refresh"]
    assert refresh_response.data["refresh"] != original_refresh

    refreshed_jti = JWTRefreshToken(refresh_response.data["refresh"])["jti"]
    old_record = RefreshToken.objects.get(key=original_jti)
    assert old_record.revoked_at is not None
    assert RefreshToken.objects.filter(key=refreshed_jti, revoked_at__isnull=True).exists()


@pytest.mark.django_db
@pytest.mark.unit
def test_refresh_rejects_invalid_token():
    client = APIClient()

    response = client.post(
        reverse("auth-refresh"),
        {"refresh_token": "not-a-valid-token"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["detail"] == "Invalid or expired refresh token"


@pytest.mark.django_db
@pytest.mark.unit
def test_refresh_rejects_revoked_token_record():
    org, _, password = _create_user_with_password()
    client = APIClient()

    login_response = client.post(
        reverse("auth-login"),
        {
            "org_id": org.id,
            "email": "admin@example.com",
            "password": password,
        },
        format="json",
    )
    refresh_value = login_response.data["refresh"]
    refresh_jti = JWTRefreshToken(refresh_value)["jti"]
    RefreshToken.objects.filter(key=refresh_jti).update(revoked_at=timezone.now())

    response = client.post(
        reverse("auth-refresh"),
        {"refresh_token": refresh_value},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["detail"] == "Invalid or expired refresh token"


@pytest.mark.django_db
@pytest.mark.unit
def test_logout_revokes_all_active_refresh_tokens_for_authenticated_user():
    org, _, password = _create_user_with_password()
    client = APIClient()

    first_login = client.post(
        reverse("auth-login"),
        {"org_id": org.id, "email": "admin@example.com", "password": password},
        format="json",
    )
    second_login = client.post(
        reverse("auth-login"),
        {"org_id": org.id, "email": "admin@example.com", "password": password},
        format="json",
    )
    assert first_login.status_code == status.HTTP_200_OK
    assert second_login.status_code == status.HTTP_200_OK

    access_token = first_login.data["access"]
    assert RefreshToken.objects.filter(revoked_at__isnull=True).count() >= 2

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    logout_response = client.post(reverse("auth-logout"), {}, format="json")

    assert logout_response.status_code == status.HTTP_204_NO_CONTENT
    assert RefreshToken.objects.filter(revoked_at__isnull=True).count() == 0


@pytest.mark.django_db
@pytest.mark.unit
def test_logout_with_invalid_bearer_token_returns_401():
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.value")

    response = client.post(reverse("auth-logout"), {}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
