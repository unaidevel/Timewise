import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "approvals",
            "0002_rename_product_app_created_f08ea1_idx_approvals_a_created_92cc62_idx_and_more",
        ),
        ("timekeeping", "0001_initial"),
        ("tenants", "0001_initial"),
        ("authz", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ApprovalModel",
        ),
        migrations.CreateModel(
            name="TimeReportApprovalModel",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
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
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="report_approvals",
                        to="tenants.tenantmodel",
                    ),
                ),
                (
                    "report",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="approval",
                        to="timekeeping.timereportmodel",
                    ),
                ),
                (
                    "reviewer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_report_approvals",
                        to="authz.authusermodel",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_report_approvals",
                        to="authz.authusermodel",
                    ),
                ),
            ],
            options={
                "db_table": "approvals_TimeReportApproval",
                "indexes": [
                    models.Index(
                        fields=["tenant", "status"],
                        name="approvals_T_tenant_status_idx",
                    ),
                    models.Index(
                        fields=["tenant", "created_at"],
                        name="approvals_T_tenant_created_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="TimeReportApprovalEventModel",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("submitted", "Submitted"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                        ],
                        max_length=20,
                    ),
                ),
                ("reason", models.TextField(blank=True, default="")),
                ("actioned_at", models.DateTimeField(auto_now_add=True)),
                (
                    "approval",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="approvals.timereportapprovalmodel",
                    ),
                ),
                (
                    "actor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="approval_events",
                        to="authz.authusermodel",
                    ),
                ),
            ],
            options={
                "db_table": "approvals_TimeReportApprovalEvent",
                "indexes": [
                    models.Index(
                        fields=["approval", "actioned_at"],
                        name="approvals_E_approval_actioned_idx",
                    ),
                ],
            },
        ),
    ]
