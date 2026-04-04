from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_refresh_tokens"),
    ]

    operations = [
        migrations.CreateModel(
            name="InviteToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.CharField(max_length=64, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invite_tokens", to="core.user"),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="invitetoken",
            index=models.Index(fields=["user", "expires_at"], name="invite_user_exp_idx"),
        ),
    ]
