from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_invite_tokens"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProperty",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_primary", models.BooleanField(default=False)),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                (
                    "property",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="user_properties", to="core.property"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="user_properties", to="core.user"),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="userproperty",
            constraint=models.UniqueConstraint(fields=("user", "property"), name="uniq_user_property"),
        ),
    ]
