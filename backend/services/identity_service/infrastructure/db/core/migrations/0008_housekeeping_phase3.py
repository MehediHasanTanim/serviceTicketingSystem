from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_housekeeping"),
    ]

    operations = [
        migrations.AddField(
            model_name="housekeepingtask",
            name="created_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="created_housekeeping_tasks", to="core.user"),
        ),
        migrations.RenameField(
            model_name="housekeepingtask",
            old_name="due_time",
            new_name="due_at",
        ),
        migrations.RemoveIndex(model_name="housekeepingtask", name="hk_task_due_time_idx"),
        migrations.AddIndex(model_name="housekeepingtask", index=models.Index(fields=["due_at"], name="hk_task_due_time_idx")),
        migrations.AlterField(
            model_name="housekeepingtask",
            name="task_type",
            field=models.CharField(
                choices=[
                    ("CLEANING", "Cleaning"),
                    ("INSPECTION", "Inspection"),
                    ("DEEP_CLEAN", "Deep Clean"),
                    ("TURNDOWN", "Turndown"),
                    ("MAINTENANCE_SUPPORT", "Maintenance Support"),
                ],
                max_length=32,
            ),
        ),
        migrations.RenameField(
            model_name="roomstatus",
            old_name="current_status",
            new_name="occupancy_status",
        ),
        migrations.AlterField(
            model_name="roomstatus",
            name="occupancy_status",
            field=models.CharField(
                choices=[
                    ("OCCUPIED", "Occupied"),
                    ("VACANT", "Vacant"),
                    ("RESERVED", "Reserved"),
                    ("OUT_OF_ORDER", "Out Of Order"),
                ],
                default="VACANT",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="roomstatus",
            name="housekeeping_status",
            field=models.CharField(
                choices=[
                    ("CLEAN", "Clean"),
                    ("DIRTY", "Dirty"),
                    ("INSPECTING", "Inspecting"),
                    ("READY", "Ready"),
                    ("BLOCKED", "Blocked"),
                ],
                default="DIRTY",
                max_length=32,
            ),
        ),
        migrations.RemoveIndex(model_name="roomstatus", name="room_status_current_idx"),
        migrations.AddIndex(model_name="roomstatus", index=models.Index(fields=["occupancy_status"], name="room_status_occupancy_idx")),
        migrations.RenameField(
            model_name="roomstatushistory",
            old_name="previous_status",
            new_name="previous_occupancy_status",
        ),
        migrations.RenameField(
            model_name="roomstatushistory",
            old_name="new_status",
            new_name="new_occupancy_status",
        ),
        migrations.AlterField(
            model_name="roomstatushistory",
            name="previous_occupancy_status",
            field=models.CharField(
                choices=[
                    ("OCCUPIED", "Occupied"),
                    ("VACANT", "Vacant"),
                    ("RESERVED", "Reserved"),
                    ("OUT_OF_ORDER", "Out Of Order"),
                ],
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="roomstatushistory",
            name="new_occupancy_status",
            field=models.CharField(
                choices=[
                    ("OCCUPIED", "Occupied"),
                    ("VACANT", "Vacant"),
                    ("RESERVED", "Reserved"),
                    ("OUT_OF_ORDER", "Out Of Order"),
                ],
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="roomstatushistory",
            name="previous_housekeeping_status",
            field=models.CharField(choices=[("CLEAN", "Clean"), ("DIRTY", "Dirty"), ("INSPECTING", "Inspecting"), ("READY", "Ready"), ("BLOCKED", "Blocked")], default="DIRTY", max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="roomstatushistory",
            name="new_housekeeping_status",
            field=models.CharField(choices=[("CLEAN", "Clean"), ("DIRTY", "Dirty"), ("INSPECTING", "Inspecting"), ("READY", "Ready"), ("BLOCKED", "Blocked")], default="DIRTY", max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="pmssynclog",
            name="error_message",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="pmssynclog",
            name="external_reference_id",
            field=models.CharField(blank=True, default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="pmssynclog",
            name="status",
            field=models.CharField(default="SUCCESS", max_length=32),
        ),
    ]
