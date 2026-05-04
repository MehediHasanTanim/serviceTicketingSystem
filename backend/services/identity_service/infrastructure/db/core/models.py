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


class UserCredential(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="credential")
    password_hash = models.CharField(max_length=255)
    last_password_change_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


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


class UserProperty(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="user_properties")
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="user_properties")
    is_primary = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "property"], name="uniq_user_property"),
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


class AuthToken(models.Model):
    key = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="auth_tokens")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["user", "expires_at"], name="auth_user_exp_idx"),
        ]


class RefreshToken(models.Model):
    key = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refresh_tokens")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "expires_at"], name="refresh_user_exp_idx"),
        ]


class ServiceOrder(TimestampedModel):
    PRIORITY_LOW = "LOW"
    PRIORITY_MEDIUM = "MEDIUM"
    PRIORITY_HIGH = "HIGH"
    PRIORITY_URGENT = "URGENT"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_URGENT, "Urgent"),
    ]

    TYPE_INSTALLATION = "INSTALLATION"
    TYPE_REPAIR = "REPAIR"
    TYPE_MAINTENANCE = "MAINTENANCE"
    TYPE_INSPECTION = "INSPECTION"
    TYPE_OTHER = "OTHER"
    TYPE_CHOICES = [
        (TYPE_INSTALLATION, "Installation"),
        (TYPE_REPAIR, "Repair"),
        (TYPE_MAINTENANCE, "Maintenance"),
        (TYPE_INSPECTION, "Inspection"),
        (TYPE_OTHER, "Other"),
    ]

    STATUS_OPEN = "OPEN"
    STATUS_ASSIGNED = "ASSIGNED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_ON_HOLD = "ON_HOLD"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_DEFERRED = "DEFERRED"
    STATUS_VOID = "VOID"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_ASSIGNED, "Assigned"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_ON_HOLD, "On Hold"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_DEFERRED, "Deferred"),
        (STATUS_VOID, "Void"),
    ]

    org = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="service_orders")
    ticket_number = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    customer_id = models.BigIntegerField()
    asset_id = models.BigIntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_service_orders")
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="assigned_service_orders",
        null=True,
        blank=True,
    )
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    type = models.CharField(max_length=32, choices=TYPE_CHOICES, default=TYPE_OTHER)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN)
    due_date = models.DateField(null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    parts_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    compensation_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    version = models.PositiveIntegerField(default=1)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["org", "status"], name="svc_order_org_status_idx"),
            models.Index(fields=["org", "priority"], name="svc_order_org_priority_idx"),
            models.Index(fields=["org", "type"], name="svc_order_org_type_idx"),
            models.Index(fields=["org", "assigned_to"], name="svc_order_org_assignee_idx"),
            models.Index(fields=["org", "customer_id"], name="svc_order_org_customer_idx"),
            models.Index(fields=["org", "created_at"], name="svc_order_org_created_idx"),
        ]


class ServiceOrderStatusHistory(models.Model):
    service_order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=16, choices=ServiceOrder.STATUS_CHOICES)
    to_status = models.CharField(max_length=16, choices=ServiceOrder.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="service_order_status_changes")
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["service_order", "changed_at"], name="svc_order_status_hist_idx"),
        ]


class ServiceOrderAssignmentHistory(models.Model):
    service_order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name="assignment_history")
    previous_assignee = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="service_order_previous_assignments",
        null=True,
        blank=True,
    )
    new_assignee = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="service_order_new_assignments",
    )
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="service_order_assignment_changes")
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["service_order", "changed_at"], name="svc_order_assign_hist_idx"),
        ]


class ServiceOrderAttachment(models.Model):
    service_order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name="attachments")
    file_name = models.CharField(max_length=255)
    storage_key = models.CharField(max_length=512)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="service_order_uploads")
    uploaded_at = models.DateTimeField(auto_now_add=True)


class ServiceOrderRemark(models.Model):
    service_order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name="remarks")
    text = models.TextField()
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name="service_order_remarks")
    is_internal = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RoomStatus(TimestampedModel):
    OCCUPANCY_OCCUPIED = "OCCUPIED"
    OCCUPANCY_VACANT = "VACANT"
    OCCUPANCY_RESERVED = "RESERVED"
    OCCUPANCY_OUT_OF_ORDER = "OUT_OF_ORDER"
    OCCUPANCY_STATUS_CHOICES = [
        (OCCUPANCY_OCCUPIED, "Occupied"),
        (OCCUPANCY_VACANT, "Vacant"),
        (OCCUPANCY_RESERVED, "Reserved"),
        (OCCUPANCY_OUT_OF_ORDER, "Out Of Order"),
    ]

    HK_CLEAN = "CLEAN"
    HK_DIRTY = "DIRTY"
    HK_INSPECTING = "INSPECTING"
    HK_READY = "READY"
    HK_BLOCKED = "BLOCKED"
    HK_STATUS_CHOICES = [
        (HK_CLEAN, "Clean"),
        (HK_DIRTY, "Dirty"),
        (HK_INSPECTING, "Inspecting"),
        (HK_READY, "Ready"),
        (HK_BLOCKED, "Blocked"),
    ]

    PRIORITY_LOW = "LOW"
    PRIORITY_MEDIUM = "MEDIUM"
    PRIORITY_HIGH = "HIGH"
    PRIORITY_URGENT = "URGENT"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_URGENT, "Urgent"),
    ]

    room = models.OneToOneField(Room, on_delete=models.CASCADE, related_name="room_status")
    occupancy_status = models.CharField(max_length=32, choices=OCCUPANCY_STATUS_CHOICES, default=OCCUPANCY_VACANT)
    housekeeping_status = models.CharField(max_length=32, choices=HK_STATUS_CHOICES, default=HK_DIRTY)
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    last_cleaned_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="room_status_updates", null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["occupancy_status"], name="room_status_occupancy_idx"),
            models.Index(fields=["housekeeping_status"], name="room_status_hk_idx"),
        ]


class RoomStatusHistory(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="room_status_history")
    previous_occupancy_status = models.CharField(max_length=32, choices=RoomStatus.OCCUPANCY_STATUS_CHOICES)
    new_occupancy_status = models.CharField(max_length=32, choices=RoomStatus.OCCUPANCY_STATUS_CHOICES)
    previous_housekeeping_status = models.CharField(max_length=32, choices=RoomStatus.HK_STATUS_CHOICES)
    new_housekeeping_status = models.CharField(max_length=32, choices=RoomStatus.HK_STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="room_status_changes", null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["room", "changed_at"], name="room_status_hist_idx"),
        ]


class HousekeepingTask(TimestampedModel):
    TYPE_CLEANING = "CLEANING"
    TYPE_INSPECTION = "INSPECTION"
    TYPE_DEEP_CLEAN = "DEEP_CLEAN"
    TYPE_MAINTENANCE_SUPPORT = "MAINTENANCE_SUPPORT"
    TYPE_TURNDOWN = "TURNDOWN"
    TYPE_CHOICES = [
        (TYPE_CLEANING, "Cleaning"),
        (TYPE_INSPECTION, "Inspection"),
        (TYPE_DEEP_CLEAN, "Deep Clean"),
        (TYPE_TURNDOWN, "Turndown"),
        (TYPE_MAINTENANCE_SUPPORT, "Maintenance Support"),
    ]

    PRIORITY_LOW = "LOW"
    PRIORITY_MEDIUM = "MEDIUM"
    PRIORITY_HIGH = "HIGH"
    PRIORITY_URGENT = "URGENT"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_URGENT, "Urgent"),
    ]

    STATUS_PENDING = "PENDING"
    STATUS_ASSIGNED = "ASSIGNED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ASSIGNED, "Assigned"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="housekeeping_tasks")
    task_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    assigned_to = models.ForeignKey(User, on_delete=models.PROTECT, related_name="housekeeping_tasks", null=True, blank=True)
    due_at = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_housekeeping_tasks", null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["room", "status"], name="hk_task_room_status_idx"),
            models.Index(fields=["assigned_to", "status"], name="hk_task_assignee_status_idx"),
            models.Index(fields=["due_at"], name="hk_task_due_time_idx"),
        ]


class HousekeepingTaskAssignmentHistory(models.Model):
    task = models.ForeignKey(HousekeepingTask, on_delete=models.CASCADE, related_name="assignment_history")
    previous_assignee = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="hk_previous_assignments",
        null=True,
        blank=True,
    )
    new_assignee = models.ForeignKey(User, on_delete=models.PROTECT, related_name="hk_new_assignments")
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="hk_assignment_changes", null=True, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["task", "changed_at"], name="hk_assign_hist_idx"),
        ]


class PMSSyncLog(models.Model):
    source = models.CharField(max_length=64)
    event_key = models.CharField(max_length=255)
    payload_json = models.JSONField(default=dict, blank=True)
    external_reference_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=32, default="SUCCESS")
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source", "event_key"], name="uniq_pms_sync_event"),
        ]
        indexes = [
            models.Index(fields=["source", "created_at"], name="pms_sync_source_created_idx"),
        ]


class PasswordResetToken(models.Model):
    token = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_tokens")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)


class InviteToken(models.Model):
    token = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invite_tokens")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "expires_at"], name="invite_user_exp_idx"),
        ]
