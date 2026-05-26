from decimal import Decimal

from django.db import models

from infra.authz.models import AuthUserModel
from infra.tenants.models import TenantModel
from product.common.classes import ApprovalAction, ApprovalStatus
from product.timekeeping.models import TimeReportModel


class TimeReportApprovalModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        TenantModel,
        on_delete=models.CASCADE,
        related_name="report_approvals",
    )
    report = models.OneToOneField(
        TimeReportModel,
        on_delete=models.CASCADE,
        related_name="approval",
    )
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    reviewer = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_report_approvals",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_report_approvals",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "approvals_TimeReportApproval"
        verbose_name = "Time report approval"
        verbose_name_plural = "Time report approvals"
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Approval {self.id} — report {self.report_id} ({self.status})"

    @property
    def report_status(self) -> str:
        return self.report.status

    @property
    def report_submitted_at(self):
        return self.report.submitted_at

    @property
    def period_name(self) -> str:
        return self.report.period.name

    @property
    def employee_full_name(self) -> str:
        return self.report.employee.full_name

    @property
    def total_hours(self) -> Decimal:
        return getattr(self, "_total_hours", None) or Decimal("0")


class TimeReportApprovalEventModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    approval = models.ForeignKey(
        TimeReportApprovalModel,
        on_delete=models.CASCADE,
        related_name="events",
    )
    action = models.CharField(max_length=20, choices=ApprovalAction.choices)
    actor = models.ForeignKey(
        AuthUserModel,
        on_delete=models.PROTECT,
        related_name="approval_events",
    )
    reason = models.TextField(blank=True, default="")
    actioned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "approvals_TimeReportApprovalEvent"
        verbose_name = "Approval event"
        verbose_name_plural = "Approval events"
        indexes = [
            models.Index(fields=["approval", "actioned_at"]),
        ]

    def __str__(self) -> str:
        return f"Event {self.id} — {self.action} by {self.actor_id} on approval {self.approval_id}"
