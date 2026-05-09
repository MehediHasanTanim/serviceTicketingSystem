# Covers: BE-AUTH-001, BE-AUTH-002, BE-AUTH-003, BE-AUTH-004, BE-AUTH-005
import pytest

from tests.unit.test_api_me_endpoint import test_me_requires_authentication
from tests.unit.test_auth_jwt_flows import (
    test_login_issues_jwt_pair_and_persists_refresh_record,
    test_login_rejects_invalid_credentials,
    test_logout_revokes_all_active_refresh_tokens_for_authenticated_user,
    test_refresh_rotates_token_and_revokes_previous_refresh_record,
)


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.auth
@pytest.mark.django_db
def test_be_auth_001_login_success_returns_tokens():
    test_login_issues_jwt_pair_and_persists_refresh_record()


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.auth
@pytest.mark.django_db
def test_be_auth_002_login_invalid_password_rejected():
    test_login_rejects_invalid_credentials()


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.auth
@pytest.mark.django_db
def test_be_auth_003_refresh_rotation_works():
    test_refresh_rotates_token_and_revokes_previous_refresh_record()


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.auth
@pytest.mark.django_db
def test_be_auth_004_logout_invalidates_refresh_tokens():
    test_logout_revokes_all_active_refresh_tokens_for_authenticated_user()


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.auth
@pytest.mark.django_db
def test_be_auth_005_protected_endpoint_rejects_missing_or_invalid_token():
    test_me_requires_authentication()
