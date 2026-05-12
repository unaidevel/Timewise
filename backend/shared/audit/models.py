from django.db import models

from infra.authz.models import AuthUserModel
from infra.tenants.models import TenantModel
from shared.audit.utils import AuditOutcome


class AuditEventModel(models.Model):
    """
    Append-only domain event log.

    Records are intentionally retained; only the free-form `notes` field
    is mutable, so the immutable history is preserved while still allowing
    operators to attach context after the fact.
    """

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        TenantModel,
        on_delete=models.CASCADE,
        related_name="audit_events",
    )
    actor = models.ForeignKey(
        AuthUserModel,
        on_delete=models.PROTECT,
        related_name="audit_events",
    )
    action = models.CharField(max_length=100)
    outcome = models.CharField(
        max_length=10,
        choices=AuditOutcome.choices,
        default=AuditOutcome.SUCCESS,
    )
    resource_type = models.CharField(max_length=100)
    resource_id = models.BigIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True, default="")
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_AuditEvent"
        indexes = [
            models.Index(fields=["tenant", "occurred_at"]),
            models.Index(fields=["tenant", "action"]),
            models.Index(fields=["tenant", "outcome"]),
            models.Index(fields=["tenant", "resource_type", "resource_id"]),
            models.Index(fields=["actor", "occurred_at"]),
        ]

    def __str__(self) -> str:
        return f"AuditEvent {self.id} — {self.action} ({self.outcome})"
