import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AuthUserModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("full_name", models.CharField(max_length=200)),
                ("password_hash", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "authz_users",
            },
        ),
        migrations.CreateModel(
            name="AuthTokenModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("expires_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tokens",
                        to="authz.authusermodel",
                    ),
                ),
            ],
            options={
                "db_table": "authz_tokens",
            },
        ),
        migrations.AddIndex(
            model_name="authusermodel",
            index=models.Index(fields=["email"], name="authz_users_email_81ee10_idx"),
        ),
        migrations.AddIndex(
            model_name="authusermodel",
            index=models.Index(
                fields=["is_active"], name="authz_users_is_acti_f34988_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="authtokenmodel",
            index=models.Index(
                fields=["expires_at"], name="authz_token_expires_bc05cf_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="authtokenmodel",
            index=models.Index(
                fields=["revoked_at"], name="authz_token_revoked_be88c3_idx"
            ),
        ),
    ]
