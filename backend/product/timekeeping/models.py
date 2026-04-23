from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from infra.authz.models import AuthUserModel
from infra.tenants.models import TenantModel
from product.common.classes import PeriodStatus, TimeReportStatus
from product.workforce.models import EmployeeModel


class PeriodModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        TenantModel,
        on_delete=models.CASCADE,
        related_name="periods",
    )
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=PeriodStatus.choices,
        default=PeriodStatus.OPEN,
    )
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="locked_periods",
    )
    created_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_periods",
    )
    updated_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_periods",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "timekeeping_periods"
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "start_date", "end_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_period_name_per_tenant",
            ),
            models.UniqueConstraint(
                fields=["tenant", "start_date", "end_date"],
                name="unique_period_dates_per_tenant",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.status})"


class TimeReportModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        TenantModel,
        on_delete=models.CASCADE,
        related_name="time_reports",
    )
    employee = models.ForeignKey(
        EmployeeModel,
        on_delete=models.PROTECT,
        related_name="time_reports",
    )
    period = models.ForeignKey(
        PeriodModel,
        on_delete=models.PROTECT,
        related_name="reports",
    )
    status = models.CharField(
        max_length=15,
        choices=TimeReportStatus.choices,
        default=TimeReportStatus.DRAFT,
    )
    version = models.PositiveIntegerField(default=0)
    rejection_reason = models.TextField(blank=True, default="")
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_time_reports",
    )
    updated_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_time_reports",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "timekeeping_reports"
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["employee", "period"]),
            models.Index(fields=["period", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "period"],
                name="unique_report_per_employee_per_period",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Report {self.id} — {self.employee_id} / {self.period_id} ({self.status})"
        )


class TimeEntryModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    report = models.ForeignKey(
        TimeReportModel,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    date = models.DateField()
    hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
            MaxValueValidator(Decimal("24")),
        ],
    )
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    description = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_time_entries",
    )
    updated_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_time_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "timekeeping_entries"
        indexes = [
            models.Index(fields=["report", "date"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    hours__gte=Decimal("0.01"), hours__lte=Decimal("24")
                ),
                name="timekeeping_entry_hours_range",
            ),
        ]

    def __str__(self) -> str:
        return f"Entry {self.id} — {self.date} ({self.hours}h)"


class TimeReportStatusHistoryModel(models.Model):
    """
    Append-only log of every status transition on a report.
    Rows are never modified after creation.
    """

    id = models.BigAutoField(primary_key=True)
    report = models.ForeignKey(
        TimeReportModel,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    from_status = models.CharField(max_length=15, null=True, blank=True)
    to_status = models.CharField(max_length=15)
    changed_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.PROTECT,
        related_name="report_status_changes",
    )
    reason = models.TextField(blank=True, default="")
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "timekeeping_report_status_history"
        indexes = [
            models.Index(fields=["report", "changed_at"]),
        ]

    def __str__(self) -> str:
        return f"Report {self.report_id}: {self.from_status} → {self.to_status}"


class TimeEntryChangeHistoryModel(models.Model):
    """
    Append-only log of field-level edits to time entries.
    Rows are never modified after creation.
    """

    id = models.BigAutoField(primary_key=True)
    entry = models.ForeignKey(
        TimeEntryModel,
        on_delete=models.CASCADE,
        related_name="change_history",
    )
    field_name = models.CharField(max_length=50)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    changed_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.PROTECT,
        related_name="entry_changes",
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "timekeeping_entry_change_history"
        indexes = [
            models.Index(fields=["entry", "changed_at"]),
        ]

    def __str__(self) -> str:
        return f"Entry {self.entry_id}: {self.field_name} changed"
