from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_asset_assetlifecyclehistory_maintenancelogbookentry_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="MaintenanceTaskAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file_name", models.CharField(max_length=255)),
                ("storage_key", models.CharField(max_length=512)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("maintenance_task", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="core.maintenancetask")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="maintenance_task_uploads", to="core.user")),
            ],
        ),
    ]
