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


class Asset(TimestampedModel):
    STATUS_ACTIVE = "ACTIVE"
    STATUS_INACTIVE = "INACTIVE"
    STATUS_UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
    STATUS_OUT_OF_SERVICE = "OUT_OF_SERVICE"
    STATUS_RETIRED = "RETIRED"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
        (STATUS_UNDER_MAINTENANCE, "Under Maintenance"),
        (STATUS_OUT_OF_SERVICE, "Out Of Service"),
        (STATUS_RETIRED, "Retired"),
    ]

    CRITICALITY_LOW = "LOW"
    CRITICALITY_MEDIUM = "MEDIUM"
    CRITICALITY_HIGH = "HIGH"
    CRITICALITY_CRITICAL = "CRITICAL"
    CRITICALITY_CHOICES = [
        (CRITICALITY_LOW, "Low"),
        (CRITICALITY_MEDIUM, "Medium"),
        (CRITICALITY_HIGH, "High"),
        (CRITICALITY_CRITICAL, "Critical"),
    ]

    org = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="assets")
    asset_code = models.CharField(max_length=64, unique=True)
    qr_code = models.CharField(max_length=255, null=True, blank=True, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=128, blank=True)
    location_id = models.BigIntegerField(null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="assets", null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="assets", null=True, blank=True)
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="assets", null=True, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    model_number = models.CharField(max_length=255, blank=True)
    serial_number = models.CharField(max_length=255, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    warranty_expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    criticality = models.CharField(max_length=16, choices=CRITICALITY_CHOICES, default=CRITICALITY_MEDIUM)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_assets")
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="updated_assets")

    class Meta:
        indexes = [
            models.Index(fields=["org", "status"], name="asset_org_status_idx"),
            models.Index(fields=["org", "category"], name="asset_org_category_idx"),
            models.Index(fields=["org", "property"], name="asset_org_property_idx"),
            models.Index(fields=["org", "room"], name="asset_org_room_idx"),
            models.Index(fields=["org", "department"], name="asset_org_dept_idx"),
            models.Index(fields=["org", "criticality"], name="asset_org_criticality_idx"),
        ]


class AssetLifecycleHistory(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="lifecycle_history")
    previous_status = models.CharField(max_length=32, choices=Asset.STATUS_CHOICES)
    new_status = models.CharField(max_length=32, choices=Asset.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="asset_status_changes")
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["asset", "changed_at"], name="asset_lifecycle_hist_idx"),
        ]


class MaintenanceTask(TimestampedModel):
    TYPE_CORRECTIVE = "CORRECTIVE"
    TYPE_PREVENTIVE = "PREVENTIVE"
    TYPE_CHOICES = [
        (TYPE_CORRECTIVE, "Corrective"),
        (TYPE_PREVENTIVE, "Preventive"),
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

    STATUS_OPEN = "OPEN"
    STATUS_ASSIGNED = "ASSIGNED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_ON_HOLD = "ON_HOLD"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_VOID = "VOID"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_ASSIGNED, "Assigned"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_ON_HOLD, "On Hold"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_VOID, "Void"),
    ]

    org = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="maintenance_tasks")
    task_number = models.CharField(max_length=64, unique=True)
    task_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="maintenance_tasks", null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="maintenance_tasks", null=True, blank=True)
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="maintenance_tasks", null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="maintenance_tasks", null=True, blank=True)
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN)
    assigned_to = models.ForeignKey(User, on_delete=models.PROTECT, related_name="assigned_maintenance_tasks", null=True, blank=True)
    reported_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="reported_maintenance_tasks")
    pm_schedule = models.ForeignKey("PMSchedule", on_delete=models.SET_NULL, related_name="generated_tasks", null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    parts_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    labor_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        indexes = [
            models.Index(fields=["org", "task_type"], name="maint_task_org_type_idx"),
            models.Index(fields=["org", "status"], name="maint_task_org_status_idx"),
            models.Index(fields=["org", "priority"], name="maint_task_org_priority_idx"),
            models.Index(fields=["org", "assigned_to"], name="maint_task_org_assignee_idx"),
            models.Index(fields=["asset", "status"], name="maint_task_asset_status_idx"),
        ]


class PMSchedule(TimestampedModel):
    FREQ_DAILY = "DAILY"
    FREQ_WEEKLY = "WEEKLY"
    FREQ_MONTHLY = "MONTHLY"
    FREQ_QUARTERLY = "QUARTERLY"
    FREQ_YEARLY = "YEARLY"
    FREQ_CUSTOM = "CUSTOM"
    FREQUENCY_CHOICES = [
        (FREQ_DAILY, "Daily"),
        (FREQ_WEEKLY, "Weekly"),
        (FREQ_MONTHLY, "Monthly"),
        (FREQ_QUARTERLY, "Quarterly"),
        (FREQ_YEARLY, "Yearly"),
        (FREQ_CUSTOM, "Custom"),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="pm_schedules")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    frequency_type = models.CharField(max_length=16, choices=FREQUENCY_CHOICES)
    frequency_interval = models.PositiveIntegerField(default=1)
    next_run_at = models.DateTimeField()
    last_run_at = models.DateTimeField(null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=16, choices=MaintenanceTask.PRIORITY_CHOICES, default=MaintenanceTask.PRIORITY_MEDIUM)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_pm_schedules")

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "next_run_at"], name="pm_sched_active_next_idx"),
            models.Index(fields=["asset", "is_active"], name="pm_sched_asset_active_idx"),
        ]


class MaintenanceLogbookEntry(models.Model):
    TYPE_DIAGNOSIS = "DIAGNOSIS"
    TYPE_WORK_PERFORMED = "WORK_PERFORMED"
    TYPE_PART_USED = "PART_USED"
    TYPE_LABOR = "LABOR"
    TYPE_NOTE = "NOTE"
    TYPE_COMPLETION_SUMMARY = "COMPLETION_SUMMARY"
    ENTRY_TYPE_CHOICES = [
        (TYPE_DIAGNOSIS, "Diagnosis"),
        (TYPE_WORK_PERFORMED, "Work Performed"),
        (TYPE_PART_USED, "Part Used"),
        (TYPE_LABOR, "Labor"),
        (TYPE_NOTE, "Note"),
        (TYPE_COMPLETION_SUMMARY, "Completion Summary"),
    ]

    maintenance_task = models.ForeignKey(MaintenanceTask, on_delete=models.CASCADE, related_name="logbook_entries")
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="logbook_entries", null=True, blank=True)
    entry_type = models.CharField(max_length=32, choices=ENTRY_TYPE_CHOICES)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="maintenance_logbook_entries")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["maintenance_task", "created_at"], name="maint_logbook_task_created_idx"),
        ]


class MaintenancePartEntry(models.Model):
    logbook_entry = models.ForeignKey(MaintenanceLogbookEntry, on_delete=models.CASCADE, related_name="parts_entries")
    part_name = models.CharField(max_length=255)
    part_number = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)


class MaintenanceLaborEntry(models.Model):
    logbook_entry = models.ForeignKey(MaintenanceLogbookEntry, on_delete=models.CASCADE, related_name="labor_entries")
    technician_id = models.BigIntegerField()
    hours = models.DecimalField(max_digits=12, decimal_places=2)
    hourly_rate = models.DecimalField(max_digits=12, decimal_places=2)
    total_labor_cost = models.DecimalField(max_digits=12, decimal_places=2)


class MaintenanceTaskAttachment(models.Model):
    maintenance_task = models.ForeignKey(MaintenanceTask, on_delete=models.CASCADE, related_name="attachments")
    file_name = models.CharField(max_length=255)
    storage_key = models.CharField(max_length=512)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="maintenance_task_uploads")
    uploaded_at = models.DateTimeField(auto_now_add=True)


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


class GuestComplaint(TimestampedModel):
    CATEGORY_ROOM_CLEANLINESS = "ROOM_CLEANLINESS"
    CATEGORY_MAINTENANCE = "MAINTENANCE"
    CATEGORY_NOISE = "NOISE"
    CATEGORY_STAFF_BEHAVIOR = "STAFF_BEHAVIOR"
    CATEGORY_BILLING = "BILLING"
    CATEGORY_FOOD_BEVERAGE = "FOOD_BEVERAGE"
    CATEGORY_CHECK_IN_CHECK_OUT = "CHECK_IN_CHECK_OUT"
    CATEGORY_SAFETY_SECURITY = "SAFETY_SECURITY"
    CATEGORY_OTHER = "OTHER"
    CATEGORY_CHOICES = [
        (CATEGORY_ROOM_CLEANLINESS, "Room Cleanliness"),
        (CATEGORY_MAINTENANCE, "Maintenance"),
        (CATEGORY_NOISE, "Noise"),
        (CATEGORY_STAFF_BEHAVIOR, "Staff Behavior"),
        (CATEGORY_BILLING, "Billing"),
        (CATEGORY_FOOD_BEVERAGE, "Food & Beverage"),
        (CATEGORY_CHECK_IN_CHECK_OUT, "Check-In / Check-Out"),
        (CATEGORY_SAFETY_SECURITY, "Safety & Security"),
        (CATEGORY_OTHER, "Other"),
    ]

    SEVERITY_LOW = "LOW"
    SEVERITY_MEDIUM = "MEDIUM"
    SEVERITY_HIGH = "HIGH"
    SEVERITY_CRITICAL = "CRITICAL"
    SEVERITY_CHOICES = [
        (SEVERITY_LOW, "Low"),
        (SEVERITY_MEDIUM, "Medium"),
        (SEVERITY_HIGH, "High"),
        (SEVERITY_CRITICAL, "Critical"),
    ]

    STATUS_NEW = "NEW"
    STATUS_TRIAGED = "TRIAGED"
    STATUS_ASSIGNED = "ASSIGNED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_ESCALATED = "ESCALATED"
    STATUS_RESOLVED = "RESOLVED"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_REOPENED = "REOPENED"
    STATUS_CLOSED = "CLOSED"
    STATUS_VOID = "VOID"
    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_TRIAGED, "Triaged"),
        (STATUS_ASSIGNED, "Assigned"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_ESCALATED, "Escalated"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_REOPENED, "Reopened"),
        (STATUS_CLOSED, "Closed"),
        (STATUS_VOID, "Void"),
    ]

    SOURCE_FRONT_DESK = "FRONT_DESK"
    SOURCE_GUEST_PORTAL = "GUEST_PORTAL"
    SOURCE_PHONE = "PHONE"
    SOURCE_EMAIL = "EMAIL"
    SOURCE_STAFF = "STAFF"
    SOURCE_PMS = "PMS"
    SOURCE_OTHER = "OTHER"
    SOURCE_CHOICES = [
        (SOURCE_FRONT_DESK, "Front Desk"),
        (SOURCE_GUEST_PORTAL, "Guest Portal"),
        (SOURCE_PHONE, "Phone"),
        (SOURCE_EMAIL, "Email"),
        (SOURCE_STAFF, "Staff"),
        (SOURCE_PMS, "PMS"),
        (SOURCE_OTHER, "Other"),
    ]

    SHIFT_MORNING = "MORNING"
    SHIFT_AFTERNOON = "AFTERNOON"
    SHIFT_NIGHT = "NIGHT"
    SHIFT_CHOICES = [
        (SHIFT_MORNING, "Morning"),
        (SHIFT_AFTERNOON, "Afternoon"),
        (SHIFT_NIGHT, "Night"),
    ]

    org = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="guest_complaints")
    complaint_number = models.CharField(max_length=64, unique=True)
    guest_id = models.BigIntegerField(null=True, blank=True)
    guest_name = models.CharField(max_length=255)
    guest_contact = models.CharField(max_length=255, blank=True)
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="guest_complaints")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="guest_complaints", null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="guest_complaints", null=True, blank=True)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default=SEVERITY_MEDIUM)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_NEW)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    source = models.CharField(max_length=32, choices=SOURCE_CHOICES, default=SOURCE_FRONT_DESK)
    vip_guest = models.BooleanField(default=False)
    reported_at = models.DateTimeField(null=True, blank=True)
    shift = models.CharField(max_length=16, choices=SHIFT_CHOICES, blank=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="assigned_guest_complaints",
        null=True,
        blank=True,
    )
    escalated_to = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="escalated_guest_complaints",
        null=True,
        blank=True,
    )
    due_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    satisfaction_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    satisfaction_comment = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_guest_complaints")
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="updated_guest_complaints")
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["property", "status"], name="guest_cmp_prop_status_idx"),
            models.Index(fields=["property", "severity"], name="guest_cmp_prop_severity_idx"),
            models.Index(fields=["property", "category"], name="guest_cmp_prop_category_idx"),
            models.Index(fields=["assigned_to"], name="guest_cmp_assignee_idx"),
            models.Index(fields=["created_at"], name="guest_cmp_created_idx"),
        ]


class GuestComplaintRoutingRule(TimestampedModel):
    category = models.CharField(max_length=32, choices=GuestComplaint.CATEGORY_CHOICES)
    severity = models.CharField(max_length=16, choices=GuestComplaint.SEVERITY_CHOICES, blank=True)
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="guest_complaint_routing_rules", null=True, blank=True)
    shift = models.CharField(max_length=16, choices=GuestComplaint.SHIFT_CHOICES, blank=True)
    vip_only = models.BooleanField(default=False)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="guest_complaint_routing_rules")
    assign_to = models.ForeignKey(User, on_delete=models.PROTECT, related_name="guest_complaint_routing_rules", null=True, blank=True)
    priority = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "priority"], name="gc_rule_active_prio_idx"),
            models.Index(fields=["category", "severity"], name="gc_rule_cat_sev_idx"),
            models.Index(fields=["property", "shift"], name="gc_rule_prop_shift_idx"),
        ]


class GuestComplaintStatusHistory(models.Model):
    complaint = models.ForeignKey(GuestComplaint, on_delete=models.CASCADE, related_name="status_history")
    previous_status = models.CharField(max_length=16, choices=GuestComplaint.STATUS_CHOICES)
    new_status = models.CharField(max_length=16, choices=GuestComplaint.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="guest_complaint_status_changes")
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["complaint", "changed_at"], name="guest_cmp_hist_changed_idx"),
        ]


class GuestComplaintEscalation(models.Model):
    complaint = models.ForeignKey(GuestComplaint, on_delete=models.CASCADE, related_name="escalations")
    escalation_level = models.PositiveIntegerField(default=1)
    escalated_from = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="guest_complaint_escalated_from",
        null=True,
        blank=True,
    )
    escalated_to = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="guest_complaint_escalated_to",
        null=True,
        blank=True,
    )
    reason = models.TextField()
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="guest_complaint_escalation_triggers",
        null=True,
        blank=True,
    )
    triggered_at = models.DateTimeField(auto_now_add=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["complaint", "escalation_level", "is_active"],
                name="uniq_guest_cmp_active_escalation_level",
            ),
        ]
        indexes = [
            models.Index(fields=["complaint", "is_active"], name="guest_cmp_esc_active_idx"),
        ]


class GuestComplaintFollowUp(TimestampedModel):
    STATUS_PENDING = "PENDING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_MISSED = "MISSED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_MISSED, "Missed"),
    ]

    complaint = models.ForeignKey(GuestComplaint, on_delete=models.CASCADE, related_name="follow_ups")
    follow_up_type = models.CharField(max_length=64)
    scheduled_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="guest_complaint_followups",
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_guest_complaint_followups")

    class Meta:
        indexes = [
            models.Index(fields=["complaint", "status"], name="guest_cmp_followup_status_idx"),
            models.Index(fields=["assigned_to", "status"], name="gc_fu_assignee_status_idx"),
            models.Index(fields=["scheduled_at"], name="guest_cmp_followup_sched_idx"),
        ]
