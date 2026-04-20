from uuid import uuid4

from django.db import models

from infra.authz.models import AuthUserModel

TENANT_ROLE_OWNER = "owner"
TENANT_ROLE_ADMIN = "admin"
TENANT_ROLE_MEMBER = "member"

_ROLE_CHOICES = [
    (TENANT_ROLE_OWNER, "Owner"),
    (TENANT_ROLE_ADMIN, "Admin"),
    (TENANT_ROLE_MEMBER, "Member"),
]


class TenantModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tenants",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenants"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return self.slug


class TenantMembershipModel(models.Model):
    """
    Tabla intermedia explícita tenant ↔ user.
    Registra quién invitó a quién, cuándo entró y cuándo salió.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    tenant = models.ForeignKey(
        TenantModel,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        AuthUserModel,
        on_delete=models.CASCADE,
        related_name="tenant_memberships",
    )
    role = models.CharField(max_length=20, choices=_ROLE_CHOICES)
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invitations",
    )
    left_at = models.DateTimeField(null=True, blank=True)
    left_reason = models.TextField(blank=True, default="")

    class Meta:
        db_table = "tenant_memberships"
        indexes = [
            models.Index(fields=["tenant", "user"]),
            models.Index(fields=["tenant", "role"]),
            models.Index(fields=["left_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "user"],
                condition=models.Q(left_at__isnull=True),
                name="unique_active_tenant_membership",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user_id} @ {self.tenant_id} ({self.role})"
