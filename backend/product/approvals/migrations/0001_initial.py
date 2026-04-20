import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("authz", "0002_authloginattemptmodel_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApprovalModel",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="approvals",
                        to="authz.authusermodel",
                    ),
                ),
            ],
            options={
                "db_table": "product_approvals",
                "indexes": [
                    models.Index(
                        fields=["created_by", "created_at"],
                        name="product_app_created_f08ea1_idx",
                    ),
                    models.Index(
                        fields=["created_by", "status"],
                        name="product_app_created_d6bd58_idx",
                    ),
                ],
            },
        ),
    ]
