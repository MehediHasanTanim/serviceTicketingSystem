from types import SimpleNamespace

import pytest

from infrastructure.db.core.models import Organization, Permission, Role, RolePermission, User, UserRole
from interfaces.api.auth_views import (
    _get_normalized_roles,
    _has_permission,
    _is_admin,
    _is_super_admin,
    _require_admin,
)


def _create_user(org_id: int = 1, email: str = "user@example.com") -> User:
    org = Organization.objects.create(id=org_id, name=f"Org {org_id}", legal_name=f"Org {org_id} LLC")
    return User.objects.create(
        org=org,
        email=email,
        display_name="Test User",
        status="active",
    )


def _assign_role(user: User, role_name: str) -> Role:
    role = Role.objects.create(org=user.org, name=role_name, description="")
    UserRole.objects.create(user=user, role=role)
    return role


@pytest.mark.django_db
@pytest.mark.unit
def test_get_normalized_roles_normalizes_case_whitespace_and_underscores():
    user = _create_user()
    _assign_role(user, " SUPER_ADMIN ")
    _assign_role(user, "Front_Desk")

    normalized = _get_normalized_roles(user, user.org_id)

    assert "super admin" in normalized
    assert "front desk" in normalized


@pytest.mark.django_db
@pytest.mark.unit
def test_is_super_admin_true_when_super_admin_role_exists():
    user = _create_user()
    _assign_role(user, "Super_Admin")

    assert _is_super_admin(user, user.org_id) is True


@pytest.mark.django_db
@pytest.mark.unit
def test_is_admin_true_for_admin_and_super_admin_roles():
    admin_user = _create_user(org_id=11, email="admin@example.com")
    super_user = _create_user(org_id=12, email="super@example.com")
    _assign_role(admin_user, "admin")
    _assign_role(super_user, "super admin")

    assert _is_admin(admin_user, admin_user.org_id) is True
    assert _is_admin(super_user, super_user.org_id) is True


@pytest.mark.django_db
@pytest.mark.unit
def test_has_permission_false_for_none_or_unauthenticated_user():
    assert _has_permission(None, "users.view") is False

    anon = SimpleNamespace(is_authenticated=False)
    assert _has_permission(anon, "users.view") is False


@pytest.mark.django_db
@pytest.mark.unit
def test_has_permission_true_for_super_admin_without_permission_mapping():
    user = _create_user()
    _assign_role(user, "SUPER_ADMIN")

    assert _has_permission(user, "users.manage") is True


@pytest.mark.django_db
@pytest.mark.unit
def test_has_permission_true_when_role_permission_exists():
    user = _create_user()
    role = _assign_role(user, "admin")
    permission = Permission.objects.create(code="users.manage", description="")
    RolePermission.objects.create(role=role, permission=permission)

    assert _has_permission(user, "users.manage") is True


@pytest.mark.django_db
@pytest.mark.unit
def test_has_permission_false_when_permission_not_assigned():
    user = _create_user()
    _assign_role(user, "admin")

    assert _has_permission(user, "users.manage") is False


@pytest.mark.django_db
@pytest.mark.unit
def test_require_admin_returns_expected_value():
    user = _create_user()
    _assign_role(user, "admin")

    assert _require_admin(user, user.org_id) is True
    assert _require_admin(None, user.org_id) is False
