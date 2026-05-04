from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken

from infrastructure.db.core.models import Organization, Permission, Role, RolePermission, User, UserRole


def create_org(name: str = "Test Org") -> Organization:
    return Organization.objects.create(name=name, legal_name=f"{name} LLC")


def create_user(
    org: Organization,
    *,
    email: str,
    display_name: str = "Test User",
    status: str = "active",
) -> User:
    return User.objects.create(
        org=org,
        email=email,
        display_name=display_name,
        status=status,
    )


def assign_role(user: User, role_name: str) -> Role:
    role, _ = Role.objects.get_or_create(
        org=user.org,
        name=role_name,
        defaults={"description": ""},
    )
    UserRole.objects.get_or_create(user=user, role=role)
    return role


def grant_permissions(user: User, permission_codes: list[str], role_name: str = "manager") -> Role:
    role = assign_role(user, role_name)
    for code in permission_codes:
        perm, _ = Permission.objects.get_or_create(code=code, defaults={"description": ""})
        RolePermission.objects.get_or_create(role=role, permission=perm)
    return role


def authenticated_client(user: User) -> APIClient:
    client = APIClient()
    access_token = str(JWTRefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return client
