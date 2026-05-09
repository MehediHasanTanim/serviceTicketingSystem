import pytest

from tests.unit.api_test_helpers import authenticated_client, create_org, create_user, grant_permissions


@pytest.fixture
def regression_org():
    return create_org("Regression Org")


@pytest.fixture
def regression_admin(regression_org):
    user = create_user(regression_org, email="regression-admin@example.com")
    grant_permissions(
        user,
        [
            "users.view",
            "users.manage",
            "service_orders.view",
            "service_orders.manage",
            "housekeeping.view",
            "housekeeping.manage",
            "integrations.providers.view",
            "integrations.providers.manage",
            "integrations.jobs.view",
            "integrations.jobs.manage",
            "integrations.metrics.view",
            "audit.view",
        ],
        role_name="regression-admin",
    )
    return user


@pytest.fixture
def regression_staff(regression_org):
    return create_user(regression_org, email="regression-staff@example.com")


@pytest.fixture
def regression_client(regression_admin):
    return authenticated_client(regression_admin)
