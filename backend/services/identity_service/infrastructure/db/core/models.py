from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Organization(TimestampedModel):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="active")

    def __str__(self):
        return self.name


class Property(TimestampedModel):
    org = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="properties")
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    timezone = models.CharField(max_length=64)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=128)
    state = models.CharField(max_length=128, blank=True)
    postal_code = models.CharField(max_length=32, blank=True)
    country = models.CharField(max_length=128)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["org", "code"], name="uniq_property_code_per_org"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Building(TimestampedModel):
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="buildings")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return self.name


class Floor(TimestampedModel):
    building = models.ForeignKey(Building, on_delete=models.PROTECT, related_name="floors")
    level_number = models.IntegerField()
    name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name or str(self.level_number)


class Zone(TimestampedModel):
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="zones")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return self.name


class Room(TimestampedModel):
    STATUS_CHOICES = [
        ("available", "Available"),
        ("occupied", "Occupied"),
        ("out_of_service", "Out of Service"),
    ]

    floor = models.ForeignKey(Floor, on_delete=models.PROTECT, related_name="rooms")
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="rooms")
    zone = models.ForeignKey(Zone, on_delete=models.PROTECT, related_name="rooms", null=True, blank=True)
    room_number = models.CharField(max_length=32)
    room_type = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="available")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["property", "room_number"], name="uniq_room_number_per_property"),
        ]

    def __str__(self):
        return self.room_number


class Department(TimestampedModel):
    org = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="departments")
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="departments", null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class User(TimestampedModel):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("suspended", "Suspended"),
        ("invited", "Invited"),
    ]

    org = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="users")
    email = models.EmailField()
    phone = models.CharField(max_length=32, blank=True)
    display_name = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="active")
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["org", "email"], name="uniq_user_email_per_org"),
        ]

    def __str__(self):
        return self.display_name


class Role(TimestampedModel):
    org = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="roles")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["org", "name"], name="uniq_role_name_per_org"),
        ]

    def __str__(self):
        return self.name


class Permission(models.Model):
    code = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.code


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.PROTECT, related_name="role_permissions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["role", "permission"], name="uniq_role_permission"),
        ]


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="user_roles")
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="assigned_roles", null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="uniq_user_role"),
        ]


class UserDepartment(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="user_departments")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="user_departments")
    is_primary = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "department"], name="uniq_user_department"),
        ]


class AuditLog(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="audit_logs")
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="audit_logs", null=True, blank=True)
    actor_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="audit_logs", null=True, blank=True)
    action = models.CharField(max_length=255)
    target_type = models.CharField(max_length=255)
    target_id = models.CharField(max_length=64, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    ip_address = models.CharField(max_length=64, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["org", "created_at"], name="audit_org_created_idx"),
            models.Index(fields=["property", "created_at"], name="audit_prop_created_idx"),
        ]


class EntityHistory(models.Model):
    CHANGE_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
    ]

    org = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="entity_history")
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="entity_history", null=True, blank=True)
    actor_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="entity_history", null=True, blank=True)
    entity_type = models.CharField(max_length=255)
    entity_id = models.CharField(max_length=64)
    change_type = models.CharField(max_length=32, choices=CHANGE_CHOICES)
    before_json = models.JSONField(default=dict, blank=True)
    after_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
