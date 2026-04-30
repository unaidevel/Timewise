import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authz", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="authtokenmodel",
            name="family_id",
            field=models.CharField(db_index=True, default="", max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="authtokenmodel",
            name="client_ip",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="authtokenmodel",
            name="user_agent",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddIndex(
            model_name="authtokenmodel",
            index=models.Index(
                fields=["user", "revoked_at"],
                name="authz_AuthT_user_id_revoke_idx",
            ),
        ),
        migrations.CreateModel(
            name="AuthLoginEventModel",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("email", models.CharField(blank=True, default="", max_length=254)),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("login_success", "Login success"),
                            ("login_failure", "Login failure"),
                            ("logout", "Logout"),
                            ("refresh", "Refresh"),
                            ("refresh_reuse", "Refresh token reuse detected"),
                            ("rate_limited", "Rate limited"),
                        ],
                        max_length=32,
                    ),
                ),
                ("client_ip", models.CharField(blank=True, default="", max_length=64)),
                (
                    "user_agent",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="login_events",
                        to="authz.authusermodel",
                    ),
                ),
            ],
            options={
                "db_table": "authz_AuthLoginEvent",
                "indexes": [
                    models.Index(
                        fields=["user", "occurred_at"],
                        name="authz_AuthL_user_id_occurr_idx",
                    ),
                    models.Index(
                        fields=["email", "occurred_at"],
                        name="authz_AuthL_email_o_occurr_idx",
                    ),
                    models.Index(
                        fields=["event_type", "occurred_at"],
                        name="authz_AuthL_event_t_occurr_idx",
                    ),
                ],
            },
        ),
    ]
