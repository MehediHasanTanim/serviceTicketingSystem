import pytest
from django.urls import reverse
from rest_framework import status

from infrastructure.db.core.models import (
    Department,
    Organization,
    Permission,
    Property,
    Role,
    RolePermission,
    UserDepartment,
    UserProperty,
    UserRole,
)
from tests.unit.api_test_helpers import authenticated_client, create_org, create_user, grant_permissions


@pytest.mark.django_db
@pytest.mark.unit
def test_roles_endpoints_require_permissions():
    org = create_org("Roles Org")
    actor = create_user(org, email="actor@example.com")
    client = authenticated_client(actor)

    list_response = client.get(reverse("role-list"), {"org_id": org.id})
    create_response = client.post(
        reverse("role-list"),
        {"org_id": org.id, "name": "supervisor"},
        format="json",
    )

    assert list_response.status_code == status.HTTP_403_FORBIDDEN
    assert list_response.data["detail"] == "Permission required: roles.view"
    assert create_response.status_code == status.HTTP_403_FORBIDDEN
    assert create_response.data["detail"] == "Permission required: roles.manage"


@pytest.mark.django_db
@pytest.mark.unit
def test_roles_crud_success_when_authorized():
    org = create_org("Roles Org")
    actor = create_user(org, email="manager@example.com")
    grant_permissions(actor, ["roles.view", "roles.manage"], role_name="roles-manager")
    client = authenticated_client(actor)

    create_response = client.post(
        reverse("role-list"),
        {"org_id": org.id, "name": "supervisor", "description": "shift supervisor"},
        format="json",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    role_id = create_response.data["id"]

    list_response = client.get(reverse("role-list"), {"org_id": org.id, "q": "super"})
    assert list_response.status_code == status.HTTP_200_OK
    assert list_response.data["count"] == 1
    assert list_response.data["results"][0]["name"] == "supervisor"

    patch_response = client.patch(
        reverse("role-detail", kwargs={"role_id": role_id}),
        {"description": "updated"},
        format="json",
    )
    assert patch_response.status_code == status.HTTP_200_OK
    assert patch_response.data["description"] == "updated"

    delete_response = client.delete(reverse("role-detail", kwargs={"role_id": role_id}))
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
@pytest.mark.unit
def test_role_create_returns_conflict_for_duplicate_name():
    org = create_org("Roles Org")
    actor = create_user(org, email="manager@example.com")
    grant_permissions(actor, ["roles.manage"], role_name="roles-manager")
    Role.objects.create(org=org, name="supervisor", description="existing")
    client = authenticated_client(actor)

    response = client.post(
        reverse("role-list"),
        {"org_id": org.id, "name": "supervisor", "description": "duplicate"},
        format="json",
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.data["detail"] == "Role already exists"


@pytest.mark.django_db
@pytest.mark.unit
def test_role_delete_returns_conflict_when_role_is_in_use():
    org = create_org("Roles Org")
    actor = create_user(org, email="manager@example.com")
    grant_permissions(actor, ["roles.manage"], role_name="roles-manager")
    target_user = create_user(org, email="assigned.user@example.com")
    role = Role.objects.create(org=org, name="frontdesk", description="")
    UserRole.objects.create(user=target_user, role=role)
    client = authenticated_client(actor)

    response = client.delete(reverse("role-detail", kwargs={"role_id": role.id}))

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.data["detail"] == "Role is in use"


@pytest.mark.django_db
@pytest.mark.unit
def test_permissions_endpoints_require_permissions():
    org = create_org("Perm Org")
    actor = create_user(org, email="actor@example.com")
    client = authenticated_client(actor)

    list_response = client.get(reverse("permission-list-create"))
    create_response = client.post(
        reverse("permission-list-create"),
        {"code": "permissions.view", "description": "view permissions"},
        format="json",
    )

    assert list_response.status_code == status.HTTP_403_FORBIDDEN
    assert list_response.data["detail"] == "Permission required: permissions.view"
    assert create_response.status_code == status.HTTP_403_FORBIDDEN
    assert create_response.data["detail"] == "Permission required: permissions.manage"


@pytest.mark.django_db
@pytest.mark.unit
def test_permissions_crud_success_when_authorized():
    org = create_org("Perm Org")
    actor = create_user(org, email="perm.manager@example.com")
    grant_permissions(actor, ["permissions.view", "permissions.manage"], role_name="perm-manager")
    client = authenticated_client(actor)

    create_response = client.post(
        reverse("permission-list-create"),
        {"code": "audit.view", "description": "view audit logs"},
        format="json",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    permission_id = create_response.data["id"]

    list_response = client.get(reverse("permission-list-create"), {"q": "audit"})
    assert list_response.status_code == status.HTTP_200_OK
    assert list_response.data["count"] == 1

    patch_response = client.patch(
        reverse("permission-detail", kwargs={"permission_id": permission_id}),
        {"description": "updated"},
        format="json",
    )
    assert patch_response.status_code == status.HTTP_200_OK
    assert patch_response.data["description"] == "updated"

    delete_response = client.delete(reverse("permission-detail", kwargs={"permission_id": permission_id}))
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
@pytest.mark.unit
def test_permission_create_returns_conflict_for_duplicate_code():
    org = create_org("Perm Org")
    actor = create_user(org, email="perm.manager@example.com")
    grant_permissions(actor, ["permissions.manage"], role_name="perm-manager")
    Permission.objects.create(code="audit.view", description="existing")
    client = authenticated_client(actor)

    response = client.post(
        reverse("permission-list-create"),
        {"code": "audit.view", "description": "duplicate"},
        format="json",
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.data["detail"] == "Permission already exists"


@pytest.mark.django_db
@pytest.mark.unit
def test_permission_delete_returns_conflict_when_permission_is_in_use():
    org = create_org("Perm Org")
    actor = create_user(org, email="perm.manager@example.com")
    grant_permissions(actor, ["permissions.manage"], role_name="perm-manager")
    role = Role.objects.create(org=org, name="security", description="")
    perm = Permission.objects.create(code="security.manage", description="")
    RolePermission.objects.create(role=role, permission=perm)
    client = authenticated_client(actor)

    response = client.delete(reverse("permission-detail", kwargs={"permission_id": perm.id}))

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.data["detail"] == "Permission is in use"


@pytest.mark.django_db
@pytest.mark.unit
def test_role_permission_mapping_endpoints_assign_list_and_delete():
    org = create_org("Mapping Org")
    actor = create_user(org, email="role.manager@example.com")
    grant_permissions(actor, ["roles.manage"], role_name="roles-manager")
    role = Role.objects.create(org=org, name="front desk", description="")
    permission = Permission.objects.create(code="tickets.manage", description="")
    client = authenticated_client(actor)

    create_response = client.post(
        reverse("role-permission-list-create", kwargs={"role_id": role.id}),
        {"permission_id": permission.id},
        format="json",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    assert RolePermission.objects.filter(role=role, permission=permission).exists()

    list_response = client.get(reverse("role-permission-list-create", kwargs={"role_id": role.id}))
    assert list_response.status_code == status.HTTP_200_OK
    assert len(list_response.data) == 1
    assert list_response.data[0]["code"] == "tickets.manage"

    delete_response = client.delete(
        reverse(
            "role-permission-detail",
            kwargs={"role_id": role.id, "permission_id": permission.id},
        )
    )
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert not RolePermission.objects.filter(role=role, permission=permission).exists()


@pytest.mark.django_db
@pytest.mark.unit
def test_user_role_mapping_endpoints_assign_list_and_delete():
    org = create_org("User Mapping Org")
    actor = create_user(org, email="users.manager@example.com")
    grant_permissions(actor, ["users.manage"], role_name="users-manager")
    target_user = create_user(org, email="target.user@example.com")
    role = Role.objects.create(org=org, name="housekeeping", description="")
    client = authenticated_client(actor)

    assign_response = client.post(
        reverse("user-role-list-create", kwargs={"user_id": target_user.id}),
        {"role_id": role.id},
        format="json",
    )
    assert assign_response.status_code == status.HTTP_201_CREATED
    assert UserRole.objects.filter(user=target_user, role=role).exists()

    list_response = client.get(reverse("user-role-list-create", kwargs={"user_id": target_user.id}))
    assert list_response.status_code == status.HTTP_200_OK
    assert len(list_response.data) == 1
    assert list_response.data[0]["name"] == "housekeeping"

    remove_response = client.delete(
        reverse(
            "user-role-detail",
            kwargs={"user_id": target_user.id, "role_id": role.id},
        )
    )
    assert remove_response.status_code == status.HTTP_204_NO_CONTENT
    assert not UserRole.objects.filter(user=target_user, role=role).exists()


@pytest.mark.django_db
@pytest.mark.unit
def test_user_property_mapping_endpoints_assign_list_and_delete():
    org = create_org("User Property Mapping Org")
    actor = create_user(org, email="users.manager@example.com")
    grant_permissions(actor, ["users.manage"], role_name="users-manager")
    target_user = create_user(org, email="target.user@example.com")
    prop = Property.objects.create(
        org=org,
        code="HTL-001",
        name="Hotel One",
        timezone="UTC",
        address_line1="123 Main St",
        city="New York",
        country="United States",
    )
    client = authenticated_client(actor)

    assign_response = client.post(
        reverse("user-property-list-create", kwargs={"user_id": target_user.id}),
        {"property_id": prop.id, "is_primary": True},
        format="json",
    )
    assert assign_response.status_code == status.HTTP_201_CREATED
    assert assign_response.data["property_id"] == prop.id
    assert assign_response.data["is_primary"] is True
    assert UserProperty.objects.filter(user=target_user, property=prop).exists()

    list_response = client.get(reverse("user-property-list-create", kwargs={"user_id": target_user.id}))
    assert list_response.status_code == status.HTTP_200_OK
    assert len(list_response.data) == 1
    assert list_response.data[0]["property_id"] == prop.id
    assert list_response.data[0]["code"] == "HTL-001"
    assert list_response.data[0]["is_primary"] is True

    remove_response = client.delete(
        reverse(
            "user-property-detail",
            kwargs={"user_id": target_user.id, "property_id": prop.id},
        )
    )
    assert remove_response.status_code == status.HTTP_204_NO_CONTENT
    assert not UserProperty.objects.filter(user=target_user, property=prop).exists()


@pytest.mark.django_db
@pytest.mark.unit
def test_user_department_mapping_endpoints_assign_list_and_delete():
    org = create_org("User Department Mapping Org")
    actor = create_user(org, email="users.manager@example.com")
    grant_permissions(actor, ["users.manage"], role_name="users-manager")
    target_user = create_user(org, email="target.user@example.com")
    prop = Property.objects.create(
        org=org,
        code="HTL-002",
        name="Hotel Two",
        timezone="UTC",
        address_line1="456 Market St",
        city="Boston",
        country="United States",
    )
    dept = Department.objects.create(
        org=org,
        property=prop,
        name="Front Office",
        description="Front office staff",
    )
    client = authenticated_client(actor)

    assign_response = client.post(
        reverse("user-department-list-create", kwargs={"user_id": target_user.id}),
        {"department_id": dept.id, "is_primary": True},
        format="json",
    )
    assert assign_response.status_code == status.HTTP_201_CREATED
    assert assign_response.data["department_id"] == dept.id
    assert assign_response.data["property_id"] == prop.id
    assert assign_response.data["is_primary"] is True
    assert UserDepartment.objects.filter(user=target_user, department=dept).exists()

    list_response = client.get(reverse("user-department-list-create", kwargs={"user_id": target_user.id}))
    assert list_response.status_code == status.HTTP_200_OK
    assert len(list_response.data) == 1
    assert list_response.data[0]["department_id"] == dept.id
    assert list_response.data[0]["name"] == "Front Office"
    assert list_response.data[0]["property_id"] == prop.id
    assert list_response.data[0]["is_primary"] is True

    remove_response = client.delete(
        reverse(
            "user-department-detail",
            kwargs={"user_id": target_user.id, "department_id": dept.id},
        )
    )
    assert remove_response.status_code == status.HTTP_204_NO_CONTENT
    assert not UserDepartment.objects.filter(user=target_user, department=dept).exists()


@pytest.mark.django_db
@pytest.mark.unit
def test_organizations_endpoints_require_permissions():
    org = create_org("Org Access")
    actor = create_user(org, email="org.actor@example.com")
    client = authenticated_client(actor)

    list_response = client.get(reverse("org-list-create"))
    create_response = client.post(
        reverse("org-list-create"),
        {"name": "Northwind", "legal_name": "Northwind LLC", "status": "active"},
        format="json",
    )
    detail_response = client.get(reverse("org-detail", kwargs={"org_id": org.id}))
    patch_response = client.patch(
        reverse("org-detail", kwargs={"org_id": org.id}),
        {"name": "Org Updated"},
        format="json",
    )
    delete_response = client.delete(reverse("org-detail", kwargs={"org_id": org.id}))

    assert list_response.status_code == status.HTTP_403_FORBIDDEN
    assert list_response.data["detail"] == "Permission required: org.view"
    assert create_response.status_code == status.HTTP_403_FORBIDDEN
    assert create_response.data["detail"] == "Permission required: org.manage"
    assert detail_response.status_code == status.HTTP_403_FORBIDDEN
    assert detail_response.data["detail"] == "Permission required: org.view"
    assert patch_response.status_code == status.HTTP_403_FORBIDDEN
    assert patch_response.data["detail"] == "Permission required: org.manage"
    assert delete_response.status_code == status.HTTP_403_FORBIDDEN
    assert delete_response.data["detail"] == "Permission required: org.manage"


@pytest.mark.django_db
@pytest.mark.unit
def test_organizations_crud_and_list_behavior_when_authorized():
    org = create_org("Org Access")
    actor = create_user(org, email="org.manager@example.com")
    grant_permissions(actor, ["org.view", "org.manage"], role_name="org-manager")
    client = authenticated_client(actor)

    create_response = client.post(
        reverse("org-list-create"),
        {"name": "Northwind", "legal_name": "Northwind Holdings LLC", "status": "active"},
        format="json",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    created_org_id = create_response.data["id"]

    list_response = client.get(
        reverse("org-list-create"),
        {"q": "north", "sort_by": "name", "sort_dir": "asc", "page": 1, "page_size": 10},
    )
    assert list_response.status_code == status.HTTP_200_OK
    assert list_response.data["count"] == 1
    assert list_response.data["results"][0]["name"] == "Northwind"

    detail_response = client.get(reverse("org-detail", kwargs={"org_id": created_org_id}))
    assert detail_response.status_code == status.HTTP_200_OK
    assert detail_response.data["legal_name"] == "Northwind Holdings LLC"


@pytest.mark.django_db
@pytest.mark.unit
def test_properties_endpoints_require_permissions():
    org = create_org("Property Access")
    actor = create_user(org, email="property.actor@example.com")
    prop = Property.objects.create(
        org=org,
        code="PROP-001",
        name="Property One",
        timezone="UTC",
        address_line1="123 Main St",
        city="New York",
        country="United States",
    )
    client = authenticated_client(actor)

    list_response = client.get(reverse("property-list-create"), {"org_id": org.id})
    create_response = client.post(
        reverse("property-list-create"),
        {
            "org_id": org.id,
            "code": "PROP-002",
            "name": "Property Two",
            "timezone": "UTC",
            "address_line1": "456 High St",
            "city": "Boston",
            "country": "United States",
        },
        format="json",
    )
    detail_response = client.get(reverse("property-detail", kwargs={"property_id": prop.id}))
    patch_response = client.patch(
        reverse("property-detail", kwargs={"property_id": prop.id}),
        {"name": "Property One Updated"},
        format="json",
    )
    delete_response = client.delete(reverse("property-detail", kwargs={"property_id": prop.id}))

    assert list_response.status_code == status.HTTP_403_FORBIDDEN
    assert list_response.data["detail"] == "Permission required: properties.view"
    assert create_response.status_code == status.HTTP_403_FORBIDDEN
    assert create_response.data["detail"] == "Permission required: properties.manage"
    assert detail_response.status_code == status.HTTP_403_FORBIDDEN
    assert detail_response.data["detail"] == "Permission required: properties.view"
    assert patch_response.status_code == status.HTTP_403_FORBIDDEN
    assert patch_response.data["detail"] == "Permission required: properties.manage"
    assert delete_response.status_code == status.HTTP_403_FORBIDDEN
    assert delete_response.data["detail"] == "Permission required: properties.manage"


@pytest.mark.django_db
@pytest.mark.unit
def test_properties_crud_and_list_behavior_when_authorized():
    org = create_org("Property Access")
    actor = create_user(org, email="property.manager@example.com")
    grant_permissions(actor, ["properties.view", "properties.manage"], role_name="property-manager")
    client = authenticated_client(actor)

    create_response = client.post(
        reverse("property-list-create"),
        {
            "org_id": org.id,
            "code": "NRT-001",
            "name": "Northwind Tower",
            "timezone": "UTC",
            "address_line1": "100 Harbor Rd",
            "city": "Seattle",
            "country": "United States",
        },
        format="json",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    property_id = create_response.data["id"]

    Property.objects.create(
        org=org,
        code="ALP-002",
        name="Alpine Suites",
        timezone="UTC",
        address_line1="55 Summit Ave",
        city="Denver",
        country="United States",
    )

    list_response = client.get(
        reverse("property-list-create"),
        {"org_id": org.id, "q": "nrt", "sort_by": "code", "sort_dir": "asc", "page": 1, "page_size": 10},
    )
    assert list_response.status_code == status.HTTP_200_OK
    assert list_response.data["count"] == 1
    assert list_response.data["results"][0]["code"] == "NRT-001"

    detail_response = client.get(reverse("property-detail", kwargs={"property_id": property_id}))
    assert detail_response.status_code == status.HTTP_200_OK
    assert detail_response.data["name"] == "Northwind Tower"

    patch_response = client.patch(
        reverse("property-detail", kwargs={"property_id": property_id}),
        {"name": "Northwind Grand Tower", "city": "Portland"},
        format="json",
    )
    assert patch_response.status_code == status.HTTP_200_OK
    assert patch_response.data["name"] == "Northwind Grand Tower"
    assert patch_response.data["city"] == "Portland"

    delete_response = client.delete(reverse("property-detail", kwargs={"property_id": property_id}))
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert not Property.objects.filter(id=property_id).exists()


@pytest.mark.django_db
@pytest.mark.unit
def test_departments_endpoints_require_permissions():
    org = create_org("Department Access")
    actor = create_user(org, email="department.actor@example.com")
    dept = Department.objects.create(org=org, name="Front Office", description="Front desk")
    client = authenticated_client(actor)

    list_response = client.get(reverse("department-list-create"), {"org_id": org.id})
    create_response = client.post(
        reverse("department-list-create"),
        {"org_id": org.id, "name": "Security", "description": "Security team"},
        format="json",
    )
    detail_response = client.get(reverse("department-detail", kwargs={"department_id": dept.id}))
    patch_response = client.patch(
        reverse("department-detail", kwargs={"department_id": dept.id}),
        {"description": "Updated description"},
        format="json",
    )
    delete_response = client.delete(reverse("department-detail", kwargs={"department_id": dept.id}))

    assert list_response.status_code == status.HTTP_403_FORBIDDEN
    assert list_response.data["detail"] == "Permission required: departments.view"
    assert create_response.status_code == status.HTTP_403_FORBIDDEN
    assert create_response.data["detail"] == "Permission required: departments.manage"
    assert detail_response.status_code == status.HTTP_403_FORBIDDEN
    assert detail_response.data["detail"] == "Permission required: departments.view"
    assert patch_response.status_code == status.HTTP_403_FORBIDDEN
    assert patch_response.data["detail"] == "Permission required: departments.manage"
    assert delete_response.status_code == status.HTTP_403_FORBIDDEN
    assert delete_response.data["detail"] == "Permission required: departments.manage"


@pytest.mark.django_db
@pytest.mark.unit
def test_departments_crud_and_list_behavior_when_authorized():
    org = create_org("Department Access")
    actor = create_user(org, email="department.manager@example.com")
    grant_permissions(actor, ["departments.view", "departments.manage"], role_name="department-manager")
    prop = Property.objects.create(
        org=org,
        code="DPT-001",
        name="Department Property",
        timezone="UTC",
        address_line1="15 Center Blvd",
        city="Chicago",
        country="United States",
    )
    client = authenticated_client(actor)

    create_response = client.post(
        reverse("department-list-create"),
        {"org_id": org.id, "property_id": prop.id, "name": "Front Office", "description": "Desk team"},
        format="json",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    department_id = create_response.data["id"]

    Department.objects.create(org=org, property=prop, name="Housekeeping", description="Room operations")

    list_response = client.get(
        reverse("department-list-create"),
        {
            "org_id": org.id,
            "property_id": prop.id,
            "q": "front",
            "sort_by": "name",
            "sort_dir": "asc",
            "page": 1,
            "page_size": 10,
        },
    )
    assert list_response.status_code == status.HTTP_200_OK
    assert list_response.data["count"] == 1
    assert list_response.data["results"][0]["name"] == "Front Office"

    detail_response = client.get(reverse("department-detail", kwargs={"department_id": department_id}))
    assert detail_response.status_code == status.HTTP_200_OK
    assert detail_response.data["property_id"] == prop.id

    patch_response = client.patch(
        reverse("department-detail", kwargs={"department_id": department_id}),
        {"description": "Updated desk team"},
        format="json",
    )
    assert patch_response.status_code == status.HTTP_200_OK
    assert patch_response.data["description"] == "Updated desk team"

    delete_response = client.delete(reverse("department-detail", kwargs={"department_id": department_id}))
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert not Department.objects.filter(id=department_id).exists()

    patch_response = client.patch(
        reverse("org-detail", kwargs={"org_id": created_org_id}),
        {"name": "Northwind Group", "status": "inactive"},
        format="json",
    )
    assert patch_response.status_code == status.HTTP_200_OK
    assert patch_response.data["name"] == "Northwind Group"
    assert patch_response.data["status"] == "inactive"

    delete_response = client.delete(reverse("org-detail", kwargs={"org_id": created_org_id}))
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert not Organization.objects.filter(id=created_org_id).exists()
