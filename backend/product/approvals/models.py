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
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Approval {self.id} — report {self.report_id} ({self.status})"


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
        indexes = [
            models.Index(fields=["approval", "actioned_at"]),
        ]

    def __str__(self) -> str:
        return f"Event {self.id} — {self.action} by {self.actor_id} on approval {self.approval_id}"
