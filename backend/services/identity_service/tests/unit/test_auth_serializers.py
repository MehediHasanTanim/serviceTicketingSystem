import pytest

from interfaces.api.serializers import (
    ActivateInviteSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    RefreshSerializer,
    ResetPasswordSerializer,
    SignupSerializer,
)


@pytest.mark.unit
def test_login_serializer_accepts_valid_payload():
    serializer = LoginSerializer(
        data={
            "org_id": 1,
            "email": "admin@example.com",
            "password": "StrongPass1!",
        }
    )

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["org_id"] == 1
    assert serializer.validated_data["email"] == "admin@example.com"


@pytest.mark.unit
@pytest.mark.parametrize(
    "payload,expected_error_field",
    [
        ({"email": "admin@example.com", "password": "StrongPass1!"}, "org_id"),
        ({"org_id": 1, "password": "StrongPass1!"}, "email"),
        ({"org_id": 1, "email": "admin@example.com"}, "password"),
        ({"org_id": 1, "email": "not-an-email", "password": "StrongPass1!"}, "email"),
    ],
)
def test_login_serializer_rejects_invalid_payload(payload, expected_error_field):
    serializer = LoginSerializer(data=payload)

    assert not serializer.is_valid()
    assert expected_error_field in serializer.errors


@pytest.mark.unit
def test_refresh_serializer_accepts_token():
    serializer = RefreshSerializer(data={"refresh_token": "some-refresh-token"})

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["refresh_token"] == "some-refresh-token"


@pytest.mark.unit
def test_refresh_serializer_rejects_blank_token():
    serializer = RefreshSerializer(data={"refresh_token": ""})

    assert not serializer.is_valid()
    assert "refresh_token" in serializer.errors


@pytest.mark.unit
def test_signup_serializer_accepts_valid_payload():
    serializer = SignupSerializer(
        data={
            "org_id": 5,
            "email": "user@example.com",
            "password": "StrongPass1!",
            "display_name": "Test User",
            "phone": "",
        }
    )

    assert serializer.is_valid(), serializer.errors


@pytest.mark.unit
def test_signup_serializer_rejects_short_password():
    serializer = SignupSerializer(
        data={
            "org_id": 5,
            "email": "user@example.com",
            "password": "short",
            "display_name": "Test User",
        }
    )

    assert not serializer.is_valid()
    assert "password" in serializer.errors


@pytest.mark.unit
def test_forgot_password_serializer_validates_email_and_org():
    serializer = ForgotPasswordSerializer(data={"org_id": 1, "email": "user@example.com"})

    assert serializer.is_valid(), serializer.errors


@pytest.mark.unit
def test_reset_password_serializer_rejects_invalid_inputs():
    serializer = ResetPasswordSerializer(
        data={
            "token": "x" * 65,
            "new_password": "short",
        }
    )

    assert not serializer.is_valid()
    assert "token" in serializer.errors
    assert "new_password" in serializer.errors


@pytest.mark.unit
def test_activate_invite_serializer_requires_minimum_password_length():
    serializer = ActivateInviteSerializer(
        data={
            "token": "x" * 64,
            "password": "short",
        }
    )

    assert not serializer.is_valid()
    assert "password" in serializer.errors
