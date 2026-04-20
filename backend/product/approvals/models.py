from django.db import models

from infra.authz.models import AuthUserModel
from product.approvals.entities.approval_entities import (
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_REJECTED,
)


class ApprovalModel(models.Model):
    STATUS_CHOICES = [
        (APPROVAL_STATUS_PENDING, "Pending"),
        (APPROVAL_STATUS_APPROVED, "Approved"),
        (APPROVAL_STATUS_REJECTED, "Rejected"),
    ]

    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=APPROVAL_STATUS_PENDING,
    )
    created_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.CASCADE,
        related_name="approvals",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_approvals"
        indexes = [
            models.Index(fields=["created_by", "created_at"]),
            models.Index(fields=["created_by", "status"]),
        ]

    def __str__(self) -> str:
        return self.title
