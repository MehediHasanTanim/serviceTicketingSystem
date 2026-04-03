from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_auth_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="RefreshToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=64, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="refresh_tokens", to="core.user"),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="refreshtoken",
            index=models.Index(fields=["user", "expires_at"], name="refresh_user_exp_idx"),
        ),
    ]
