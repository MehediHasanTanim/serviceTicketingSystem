from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("legal_name", models.CharField(max_length=255)),
                (
                    "status",
                    models.CharField(choices=[("active", "Active"), ("inactive", "Inactive")], default="active", max_length=32),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Permission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Property",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=64)),
                ("name", models.CharField(max_length=255)),
                ("timezone", models.CharField(max_length=64)),
                ("address_line1", models.CharField(max_length=255)),
                ("address_line2", models.CharField(blank=True, max_length=255)),
                ("city", models.CharField(max_length=128)),
                ("state", models.CharField(blank=True, max_length=128)),
                ("postal_code", models.CharField(blank=True, max_length=32)),
                ("country", models.CharField(max_length=128)),
                (
                    "org",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="properties", to="core.organization"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Department",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                (
                    "org",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="departments", to="core.organization"),
                ),
                (
                    "property",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="departments", to="core.property"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Role",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                (
                    "org",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="roles", to="core.organization"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(blank=True, max_length=32)),
                ("display_name", models.CharField(max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("suspended", "Suspended"), ("invited", "Invited")],
                        default="active",
                        max_length=32,
                    ),
                ),
                ("last_login_at", models.DateTimeField(blank=True, null=True)),
                (
                    "org",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="users", to="core.organization"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Building",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("code", models.CharField(blank=True, max_length=64)),
                (
                    "property",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="buildings", to="core.property"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Floor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("level_number", models.IntegerField()),
                ("name", models.CharField(blank=True, max_length=255)),
                (
                    "building",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="floors", to="core.building"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Zone",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("code", models.CharField(blank=True, max_length=64)),
                (
                    "property",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="zones", to="core.property"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Room",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("room_number", models.CharField(max_length=32)),
                ("room_type", models.CharField(blank=True, max_length=64)),
                (
                    "status",
                    models.CharField(
                        choices=[("available", "Available"), ("occupied", "Occupied"), ("out_of_service", "Out of Service")],
                        default="available",
                        max_length=32,
                    ),
                ),
                (
                    "floor",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="rooms", to="core.floor"),
                ),
                (
                    "property",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="rooms", to="core.property"),
                ),
                (
                    "zone",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="rooms", to="core.zone"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RolePermission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "permission",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="role_permissions", to="core.permission"),
                ),
                (
                    "role",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="role_permissions", to="core.role"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserRole",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                (
                    "assigned_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="assigned_roles", to="core.user"),
                ),
                (
                    "role",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="user_roles", to="core.role"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="user_roles", to="core.user"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserDepartment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_primary", models.BooleanField(default=False)),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                (
                    "department",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="user_departments", to="core.department"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="user_departments", to="core.user"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=255)),
                ("target_type", models.CharField(max_length=255)),
                ("target_id", models.CharField(blank=True, max_length=64)),
                ("metadata_json", models.JSONField(blank=True, default=dict)),
                ("ip_address", models.CharField(blank=True, max_length=64)),
                ("user_agent", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor_user",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="audit_logs", to="core.user"),
                ),
                (
                    "org",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="audit_logs", to="core.organization"),
                ),
                (
                    "property",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="audit_logs", to="core.property"),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["org", "created_at"], name="audit_org_created_idx"),
                    models.Index(fields=["property", "created_at"], name="audit_prop_created_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="EntityHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("entity_type", models.CharField(max_length=255)),
                ("entity_id", models.CharField(max_length=64)),
                (
                    "change_type",
                    models.CharField(choices=[("create", "Create"), ("update", "Update"), ("delete", "Delete")], max_length=32),
                ),
                ("before_json", models.JSONField(blank=True, default=dict)),
                ("after_json", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor_user",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="entity_history", to="core.user"),
                ),
                (
                    "org",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="entity_history", to="core.organization"),
                ),
                (
                    "property",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="entity_history", to="core.property"),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="property",
            constraint=models.UniqueConstraint(fields=("org", "code"), name="uniq_property_code_per_org"),
        ),
        migrations.AddConstraint(
            model_name="room",
            constraint=models.UniqueConstraint(fields=("property", "room_number"), name="uniq_room_number_per_property"),
        ),
        migrations.AddConstraint(
            model_name="role",
            constraint=models.UniqueConstraint(fields=("org", "name"), name="uniq_role_name_per_org"),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(fields=("org", "email"), name="uniq_user_email_per_org"),
        ),
        migrations.AddConstraint(
            model_name="rolepermission",
            constraint=models.UniqueConstraint(fields=("role", "permission"), name="uniq_role_permission"),
        ),
        migrations.AddConstraint(
            model_name="userrole",
            constraint=models.UniqueConstraint(fields=("user", "role"), name="uniq_user_role"),
        ),
        migrations.AddConstraint(
            model_name="userdepartment",
            constraint=models.UniqueConstraint(fields=("user", "department"), name="uniq_user_department"),
        ),
    ]
