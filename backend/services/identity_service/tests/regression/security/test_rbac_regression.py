# Covers: BE-RBAC-001, BE-RBAC-002, BE-RBAC-003, BE-RBAC-004
import pytest

from tests.unit.test_api_roles_permissions_mappings import test_role_permission_mapping_endpoints_assign_list_and_delete
from tests.unit.test_api_users_crud_permissions import (
    test_user_create_and_update_and_delete_success_when_authorized,
    test_user_create_requires_users_manage_permission,
)


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.rbac
@pytest.mark.django_db
def test_be_rbac_001_admin_can_create_user():
    test_user_create_and_update_and_delete_success_when_authorized()


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.rbac
@pytest.mark.django_db
def test_be_rbac_002_staff_blocked_from_user_create():
    test_user_create_requires_users_manage_permission()


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.rbac
@pytest.mark.django_db
def test_be_rbac_004_role_permission_mapping_add_remove_works():
    test_role_permission_mapping_endpoints_assign_list_and_delete()
