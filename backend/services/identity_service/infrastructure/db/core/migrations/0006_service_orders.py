from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_user_properties"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServiceOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("ticket_number", models.CharField(max_length=64, unique=True)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("customer_id", models.BigIntegerField()),
                ("asset_id", models.BigIntegerField(blank=True, null=True)),
                ("priority", models.CharField(choices=[("LOW", "Low"), ("MEDIUM", "Medium"), ("HIGH", "High"), ("URGENT", "Urgent")], default="MEDIUM", max_length=16)),
                ("type", models.CharField(choices=[("INSTALLATION", "Installation"), ("REPAIR", "Repair"), ("MAINTENANCE", "Maintenance"), ("INSPECTION", "Inspection"), ("OTHER", "Other")], default="OTHER", max_length=32)),
                ("status", models.CharField(choices=[("OPEN", "Open"), ("ASSIGNED", "Assigned"), ("IN_PROGRESS", "In Progress"), ("ON_HOLD", "On Hold"), ("COMPLETED", "Completed"), ("DEFERRED", "Deferred"), ("VOID", "Void")], default="OPEN", max_length=16)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("scheduled_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("estimated_cost", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("parts_cost", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("labor_cost", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("compensation_cost", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("total_cost", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("version", models.PositiveIntegerField(default=1)),
                ("is_deleted", models.BooleanField(default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="assigned_service_orders", to="core.user")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_service_orders", to="core.user")),
                ("org", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="service_orders", to="core.organization")),
            ],
        ),
        migrations.CreateModel(
            name="ServiceOrderAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file_name", models.CharField(max_length=255)),
                ("storage_key", models.CharField(max_length=512)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("service_order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="core.serviceorder")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="service_order_uploads", to="core.user")),
            ],
        ),
        migrations.CreateModel(
            name="ServiceOrderRemark",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField()),
                ("is_internal", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="service_order_remarks", to="core.user")),
                ("service_order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="remarks", to="core.serviceorder")),
            ],
        ),
        migrations.CreateModel(
            name="ServiceOrderStatusHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_status", models.CharField(choices=[("OPEN", "Open"), ("ASSIGNED", "Assigned"), ("IN_PROGRESS", "In Progress"), ("ON_HOLD", "On Hold"), ("COMPLETED", "Completed"), ("DEFERRED", "Deferred"), ("VOID", "Void")], max_length=16)),
                ("to_status", models.CharField(choices=[("OPEN", "Open"), ("ASSIGNED", "Assigned"), ("IN_PROGRESS", "In Progress"), ("ON_HOLD", "On Hold"), ("COMPLETED", "Completed"), ("DEFERRED", "Deferred"), ("VOID", "Void")], max_length=16)),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                ("note", models.TextField(blank=True)),
                ("changed_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="service_order_status_changes", to="core.user")),
                ("service_order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="status_history", to="core.serviceorder")),
            ],
        ),
        migrations.CreateModel(
            name="ServiceOrderAssignmentHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                ("reason", models.TextField(blank=True)),
                ("changed_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="service_order_assignment_changes", to="core.user")),
                ("new_assignee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="service_order_new_assignments", to="core.user")),
                ("previous_assignee", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="service_order_previous_assignments", to="core.user")),
                ("service_order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignment_history", to="core.serviceorder")),
            ],
        ),
        migrations.AddIndex(model_name="serviceorder", index=models.Index(fields=["org", "status"], name="svc_order_org_status_idx")),
        migrations.AddIndex(model_name="serviceorder", index=models.Index(fields=["org", "priority"], name="svc_order_org_priority_idx")),
        migrations.AddIndex(model_name="serviceorder", index=models.Index(fields=["org", "type"], name="svc_order_org_type_idx")),
        migrations.AddIndex(model_name="serviceorder", index=models.Index(fields=["org", "assigned_to"], name="svc_order_org_assignee_idx")),
        migrations.AddIndex(model_name="serviceorder", index=models.Index(fields=["org", "customer_id"], name="svc_order_org_customer_idx")),
        migrations.AddIndex(model_name="serviceorder", index=models.Index(fields=["org", "created_at"], name="svc_order_org_created_idx")),
        migrations.AddIndex(model_name="serviceorderstatushistory", index=models.Index(fields=["service_order", "changed_at"], name="svc_order_status_hist_idx")),
        migrations.AddIndex(model_name="serviceorderassignmenthistory", index=models.Index(fields=["service_order", "changed_at"], name="svc_order_assign_hist_idx")),
    ]
