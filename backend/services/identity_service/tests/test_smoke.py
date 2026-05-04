import pytest
from django.urls import reverse


@pytest.mark.unit
def test_core_auth_routes_are_registered():
    assert reverse("auth-login") == "/api/v1/auth/login"
    assert reverse("auth-me") == "/api/v1/me"
