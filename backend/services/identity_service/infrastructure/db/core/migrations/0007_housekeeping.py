from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_service_orders"),
    ]

    operations = [
        migrations.CreateModel(
            name="HousekeepingTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "task_type",
                    models.CharField(
                        choices=[
                            ("CLEANING", "Cleaning"),
                            ("INSPECTION", "Inspection"),
                            ("DEEP_CLEAN", "Deep Clean"),
                            ("MAINTENANCE_SUPPORT", "Maintenance Support"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        choices=[("LOW", "Low"), ("MEDIUM", "Medium"), ("HIGH", "High"), ("URGENT", "Urgent")],
                        default="MEDIUM",
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("ASSIGNED", "Assigned"),
                            ("IN_PROGRESS", "In Progress"),
                            ("COMPLETED", "Completed"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        default="PENDING",
                        max_length=16,
                    ),
                ),
                ("due_time", models.DateTimeField()),
                ("notes", models.TextField(blank=True)),
                (
                    "assigned_to",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="housekeeping_tasks", to="core.user"),
                ),
                ("room", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="housekeeping_tasks", to="core.room")),
            ],
        ),
        migrations.CreateModel(
            name="PMSSyncLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(max_length=64)),
                ("event_key", models.CharField(max_length=255)),
                ("payload_json", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="RoomStatus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "current_status",
                    models.CharField(
                        choices=[
                            ("CLEAN", "Clean"),
                            ("DIRTY", "Dirty"),
                            ("INSPECTING", "Inspecting"),
                            ("OUT_OF_SERVICE", "Out of Service"),
                            ("OCCUPIED", "Occupied"),
                            ("VACANT", "Vacant"),
                        ],
                        default="VACANT",
                        max_length=32,
                    ),
                ),
                (
                    "housekeeping_status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("IN_PROGRESS", "In Progress"),
                            ("COMPLETED", "Completed"),
                            ("VERIFIED", "Verified"),
                        ],
                        default="PENDING",
                        max_length=32,
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        choices=[("LOW", "Low"), ("MEDIUM", "Medium"), ("HIGH", "High"), ("URGENT", "Urgent")],
                        default="MEDIUM",
                        max_length=16,
                    ),
                ),
                ("last_cleaned_at", models.DateTimeField(blank=True, null=True)),
                ("room", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="room_status", to="core.room")),
                (
                    "updated_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="room_status_updates", to="core.user"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RoomStatusHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "previous_status",
                    models.CharField(
                        choices=[
                            ("CLEAN", "Clean"),
                            ("DIRTY", "Dirty"),
                            ("INSPECTING", "Inspecting"),
                            ("OUT_OF_SERVICE", "Out of Service"),
                            ("OCCUPIED", "Occupied"),
                            ("VACANT", "Vacant"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "new_status",
                    models.CharField(
                        choices=[
                            ("CLEAN", "Clean"),
                            ("DIRTY", "Dirty"),
                            ("INSPECTING", "Inspecting"),
                            ("OUT_OF_SERVICE", "Out of Service"),
                            ("OCCUPIED", "Occupied"),
                            ("VACANT", "Vacant"),
                        ],
                        max_length=32,
                    ),
                ),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                ("reason", models.TextField(blank=True)),
                (
                    "changed_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="room_status_changes", to="core.user"),
                ),
                ("room", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="room_status_history", to="core.room")),
            ],
        ),
        migrations.CreateModel(
            name="HousekeepingTaskAssignmentHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                ("reason", models.TextField(blank=True)),
                (
                    "changed_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="hk_assignment_changes", to="core.user"),
                ),
                (
                    "new_assignee",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="hk_new_assignments", to="core.user"),
                ),
                (
                    "previous_assignee",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="hk_previous_assignments", to="core.user"),
                ),
                (
                    "task",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignment_history", to="core.housekeepingtask"),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="pmssynclog",
            constraint=models.UniqueConstraint(fields=("source", "event_key"), name="uniq_pms_sync_event"),
        ),
        migrations.AddIndex(model_name="roomstatus", index=models.Index(fields=["current_status"], name="room_status_current_idx")),
        migrations.AddIndex(model_name="roomstatus", index=models.Index(fields=["housekeeping_status"], name="room_status_hk_idx")),
        migrations.AddIndex(model_name="roomstatushistory", index=models.Index(fields=["room", "changed_at"], name="room_status_hist_idx")),
        migrations.AddIndex(model_name="housekeepingtask", index=models.Index(fields=["room", "status"], name="hk_task_room_status_idx")),
        migrations.AddIndex(model_name="housekeepingtask", index=models.Index(fields=["assigned_to", "status"], name="hk_task_assignee_status_idx")),
        migrations.AddIndex(model_name="housekeepingtask", index=models.Index(fields=["due_time"], name="hk_task_due_time_idx")),
        migrations.AddIndex(model_name="housekeepingtaskassignmenthistory", index=models.Index(fields=["task", "changed_at"], name="hk_assign_hist_idx")),
        migrations.AddIndex(model_name="pmssynclog", index=models.Index(fields=["source", "created_at"], name="pms_sync_source_created_idx")),
    ]
