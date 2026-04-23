import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("authz", "0002_authloginattemptmodel_and_more"),
        ("tenants", "0001_initial"),
        ("workforce", "0003_created_by_updated_by"),
    ]

    operations = [
        migrations.CreateModel(
            name="PeriodModel",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[("open", "Open"), ("locked", "Locked")],
                        default="open",
                        max_length=10,
                    ),
                ),
                ("locked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="periods",
                        to="tenants.tenantmodel",
                    ),
                ),
                (
                    "locked_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="locked_periods",
                        to="authz.authusermodel",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_periods",
                        to="authz.authusermodel",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_periods",
                        to="authz.authusermodel",
                    ),
                ),
            ],
            options={
                "db_table": "timekeeping_periods",
            },
        ),
        migrations.CreateModel(
            name="TimeReportModel",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("submitted", "Submitted"),
                            ("under_review", "Under Review"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                            ("locked", "Locked"),
                        ],
                        default="draft",
                        max_length=15,
                    ),
                ),
                ("version", models.PositiveIntegerField(default=0)),
                ("rejection_reason", models.TextField(blank=True, default="")),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("rejected_at", models.DateTimeField(blank=True, null=True)),
                ("locked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="time_reports",
                        to="tenants.tenantmodel",
                    ),
                ),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="time_reports",
                        to="workforce.employeemodel",
                    ),
                ),
                (
                    "period",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reports",
                        to="timekeeping.periodmodel",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_time_reports",
                        to="authz.authusermodel",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_time_reports",
                        to="authz.authusermodel",
                    ),
                ),
            ],
            options={
                "db_table": "timekeeping_reports",
            },
        ),
        migrations.CreateModel(
            name="TimeEntryModel",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("date", models.DateField()),
                ("hours", models.DecimalField(decimal_places=2, max_digits=5)),
                ("start_time", models.TimeField(blank=True, null=True)),
                ("end_time", models.TimeField(blank=True, null=True)),
                ("description", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="entries",
                        to="timekeeping.timereportmodel",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_time_entries",
                        to="authz.authusermodel",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_time_entries",
                        to="authz.authusermodel",
                    ),
                ),
            ],
            options={
                "db_table": "timekeeping_entries",
            },
        ),
        migrations.CreateModel(
            name="TimeReportStatusHistoryModel",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("from_status", models.CharField(blank=True, max_length=15, null=True)),
                ("to_status", models.CharField(max_length=15)),
                ("reason", models.TextField(blank=True, default="")),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_history",
                        to="timekeeping.timereportmodel",
                    ),
                ),
                (
                    "changed_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="report_status_changes",
                        to="authz.authusermodel",
                    ),
                ),
            ],
            options={
                "db_table": "timekeeping_report_status_history",
            },
        ),
        migrations.CreateModel(
            name="TimeEntryChangeHistoryModel",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("field_name", models.CharField(max_length=50)),
                ("old_value", models.TextField(blank=True, null=True)),
                ("new_value", models.TextField(blank=True, null=True)),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "entry",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="change_history",
                        to="timekeeping.timeentrymodel",
                    ),
                ),
                (
                    "changed_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="entry_changes",
                        to="authz.authusermodel",
                    ),
                ),
            ],
            options={
                "db_table": "timekeeping_entry_change_history",
            },
        ),
        # Indexes
        migrations.AddIndex(
            model_name="periodmodel",
            index=models.Index(
                fields=["tenant", "status"],
                name="timekeeping_period_tenant_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="periodmodel",
            index=models.Index(
                fields=["tenant", "start_date", "end_date"],
                name="timekeeping_period_dates_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="periodmodel",
            constraint=models.UniqueConstraint(
                fields=("tenant", "name"),
                name="unique_period_name_per_tenant",
            ),
        ),
        migrations.AddConstraint(
            model_name="periodmodel",
            constraint=models.UniqueConstraint(
                fields=("tenant", "start_date", "end_date"),
                name="unique_period_dates_per_tenant",
            ),
        ),
        migrations.AddIndex(
            model_name="timereportmodel",
            index=models.Index(
                fields=["tenant", "status"],
                name="timekeeping_report_tenant_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="timereportmodel",
            index=models.Index(
                fields=["employee", "period"],
                name="timekeeping_report_emp_period_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="timereportmodel",
            index=models.Index(
                fields=["period", "status"],
                name="timekeeping_report_period_status_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="timereportmodel",
            constraint=models.UniqueConstraint(
                fields=("employee", "period"),
                name="unique_report_per_employee_per_period",
            ),
        ),
        migrations.AddIndex(
            model_name="timeentrymodel",
            index=models.Index(
                fields=["report", "date"],
                name="timekeeping_entry_report_date_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="timereportstatushistorymodel",
            index=models.Index(
                fields=["report", "changed_at"],
                name="timekeeping_status_hist_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="timeentrychangehistorymodel",
            index=models.Index(
                fields=["entry", "changed_at"],
                name="timekeeping_entry_change_idx",
            ),
        ),
    ]
