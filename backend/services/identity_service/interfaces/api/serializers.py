from rest_framework import serializers


class SignupSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    display_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)


class LoginSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class RefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class JWTPairResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    access_expires_at = serializers.DateTimeField()
    refresh_expires_at = serializers.DateTimeField()


class SignupJWTResponseSerializer(JWTPairResponseSerializer):
    user_id = serializers.IntegerField()


class ForgotPasswordSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=64)
    new_password = serializers.CharField(min_length=8, write_only=True)


class ActivateInviteSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=64)
    password = serializers.CharField(min_length=8, write_only=True)


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    org_id = serializers.IntegerField()
    email = serializers.EmailField()
    display_name = serializers.CharField(max_length=255)
    roles = serializers.ListField(child=serializers.CharField())
    is_admin = serializers.BooleanField()
    is_super_admin = serializers.BooleanField()


class UserCreateSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    email = serializers.EmailField()
    display_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=["active", "suspended", "invited"], default="invited")
    role_name = serializers.CharField(max_length=255, required=False)
    password = serializers.CharField(min_length=8, required=False, write_only=True)


class UserUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    display_name = serializers.CharField(max_length=255, required=False)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=["active", "suspended", "invited"], required=False)
    role_name = serializers.CharField(max_length=255, required=False)


class UserResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    org_id = serializers.IntegerField()
    email = serializers.EmailField()
    display_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=32, allow_blank=True)
    status = serializers.CharField()
    roles = serializers.ListField(child=serializers.CharField(), required=False)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class RoleCreateSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)


class RoleUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)


class RoleResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    org_id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class PermissionCreateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)


class PermissionUpdateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)


class PermissionResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True)


class RolePermissionAssignSerializer(serializers.Serializer):
    permission_id = serializers.IntegerField()


class OrganizationCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    legal_name = serializers.CharField(max_length=255)
    status = serializers.ChoiceField(choices=["active", "inactive"], default="active")


class OrganizationUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    legal_name = serializers.CharField(max_length=255, required=False)
    status = serializers.ChoiceField(choices=["active", "inactive"], required=False)


class OrganizationResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    legal_name = serializers.CharField(max_length=255)
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class PropertyCreateSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    code = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=255)
    timezone = serializers.CharField(max_length=64)
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=128)
    state = serializers.CharField(max_length=128, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=32, required=False, allow_blank=True)
    country = serializers.CharField(max_length=128)


class PropertyUpdateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=64, required=False)
    name = serializers.CharField(max_length=255, required=False)
    timezone = serializers.CharField(max_length=64, required=False)
    address_line1 = serializers.CharField(max_length=255, required=False)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=128, required=False)
    state = serializers.CharField(max_length=128, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=32, required=False, allow_blank=True)
    country = serializers.CharField(max_length=128, required=False)


class PropertyResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    org_id = serializers.IntegerField()
    code = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=255)
    timezone = serializers.CharField(max_length=64)
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(max_length=255, allow_blank=True)
    city = serializers.CharField(max_length=128)
    state = serializers.CharField(max_length=128, allow_blank=True)
    postal_code = serializers.CharField(max_length=32, allow_blank=True)
    country = serializers.CharField(max_length=128)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class DepartmentCreateSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    property_id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)


class DepartmentUpdateSerializer(serializers.Serializer):
    property_id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)


class DepartmentResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    org_id = serializers.IntegerField()
    property_id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class UserDepartmentAssignSerializer(serializers.Serializer):
    department_id = serializers.IntegerField()
    is_primary = serializers.BooleanField(required=False, default=False)


class UserPropertyAssignSerializer(serializers.Serializer):
    property_id = serializers.IntegerField()
    is_primary = serializers.BooleanField(required=False, default=False)


class UserRoleAssignSerializer(serializers.Serializer):
    role_id = serializers.IntegerField()


class ServiceOrderCreateSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    customer_id = serializers.IntegerField()
    asset_id = serializers.IntegerField(required=False, allow_null=True)
    assigned_to = serializers.IntegerField(required=False, allow_null=True)
    priority = serializers.ChoiceField(choices=["LOW", "MEDIUM", "HIGH", "URGENT"], default="MEDIUM")
    type = serializers.ChoiceField(
        choices=["INSTALLATION", "REPAIR", "MAINTENANCE", "INSPECTION", "OTHER"],
        default="OTHER",
    )
    due_date = serializers.DateField(required=False, allow_null=True)
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
    estimated_cost = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default="0.00")
    parts_cost = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default="0.00")
    labor_cost = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default="0.00")
    compensation_cost = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default="0.00")


class ServiceOrderUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    customer_id = serializers.IntegerField(required=False)
    asset_id = serializers.IntegerField(required=False, allow_null=True)
    priority = serializers.ChoiceField(choices=["LOW", "MEDIUM", "HIGH", "URGENT"], required=False)
    type = serializers.ChoiceField(
        choices=["INSTALLATION", "REPAIR", "MAINTENANCE", "INSPECTION", "OTHER"],
        required=False,
    )
    due_date = serializers.DateField(required=False, allow_null=True)
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
    estimated_cost = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)


class ServiceOrderResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    org_id = serializers.IntegerField()
    ticket_number = serializers.CharField(max_length=64)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True)
    customer_id = serializers.IntegerField()
    asset_id = serializers.IntegerField(required=False, allow_null=True)
    created_by = serializers.IntegerField()
    assigned_to = serializers.IntegerField(required=False, allow_null=True)
    priority = serializers.CharField()
    type = serializers.CharField()
    status = serializers.CharField()
    due_date = serializers.DateField(required=False, allow_null=True)
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
    completed_at = serializers.DateTimeField(required=False, allow_null=True)
    estimated_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    parts_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    labor_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    compensation_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    version = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class ServiceOrderAssignSerializer(serializers.Serializer):
    assignee_id = serializers.IntegerField()
    reason = serializers.CharField(required=False, allow_blank=True)


class ServiceOrderTransitionSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)


class ServiceOrderAttachmentSerializer(serializers.Serializer):
    file_name = serializers.CharField(max_length=255)
    storage_key = serializers.CharField(max_length=512)


class ServiceOrderRemarkSerializer(serializers.Serializer):
    text = serializers.CharField()
    is_internal = serializers.BooleanField(required=False, default=True)


class ServiceOrderCostUpdateSerializer(serializers.Serializer):
    parts_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    labor_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    compensation_cost = serializers.DecimalField(max_digits=12, decimal_places=2)


class RoomStatusUpsertSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    occupancy_status = serializers.ChoiceField(choices=["OCCUPIED", "VACANT", "RESERVED", "OUT_OF_ORDER"])
    housekeeping_status = serializers.ChoiceField(choices=["CLEAN", "DIRTY", "INSPECTING", "READY", "BLOCKED"])
    priority = serializers.ChoiceField(choices=["LOW", "MEDIUM", "HIGH", "URGENT"], default="MEDIUM")
    last_cleaned_at = serializers.DateTimeField(required=False, allow_null=True)
    reason = serializers.CharField(required=False, allow_blank=True)


class HousekeepingAssignSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    property_id = serializers.IntegerField()
    strategy = serializers.ChoiceField(choices=["round_robin", "least_loaded", "priority_first"])


class HousekeepingKPIFilterSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    property_id = serializers.IntegerField(required=False)
    floor_id = serializers.IntegerField(required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    staff_id = serializers.IntegerField(required=False)
    room_type = serializers.CharField(required=False)


class PMSRoomStatusSyncSerializer(serializers.Serializer):
    external_reference_id = serializers.CharField(max_length=255)
    room_id = serializers.IntegerField()
    occupancy_status = serializers.ChoiceField(choices=["OCCUPIED", "VACANT", "RESERVED", "OUT_OF_ORDER"])
    housekeeping_status = serializers.ChoiceField(choices=["CLEAN", "DIRTY", "INSPECTING", "READY", "BLOCKED"])
    timestamp = serializers.DateTimeField()


class PMSRoomStatusPullSerializer(serializers.Serializer):
    property_id = serializers.IntegerField(required=False)


class HousekeepingTaskSyncSerializer(serializers.Serializer):
    external_reference_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    task_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=["PENDING", "ASSIGNED", "IN_PROGRESS", "COMPLETED", "CANCELLED"])
    timestamp = serializers.DateTimeField()


class HousekeepingTaskListFilterSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    property_id = serializers.IntegerField(required=False)
    floor_id = serializers.IntegerField(required=False)
    room_id = serializers.IntegerField(required=False)
    assigned_to = serializers.IntegerField(required=False)
    priority = serializers.ChoiceField(choices=["LOW", "MEDIUM", "HIGH", "URGENT"], required=False)
    task_type = serializers.ChoiceField(choices=["CLEANING", "INSPECTION", "DEEP_CLEAN", "MAINTENANCE_SUPPORT", "TURNDOWN"], required=False)
    status = serializers.ChoiceField(choices=["PENDING", "ASSIGNED", "IN_PROGRESS", "COMPLETED", "CANCELLED"], required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    q = serializers.CharField(required=False, allow_blank=True)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=10)
    sort_by = serializers.ChoiceField(
        choices=["id", "priority", "status", "task_type", "due_at", "created_at", "updated_at"],
        required=False,
        default="updated_at",
    )
    sort_dir = serializers.ChoiceField(choices=["asc", "desc"], required=False, default="desc")


class HousekeepingTaskActionSerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    note = serializers.CharField(required=False, allow_blank=True)
    reason = serializers.CharField(required=False, allow_blank=True)
