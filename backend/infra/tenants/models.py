from django.db import models

from infra.authz.models import AuthUserModel
from infra.common.classes import MembershipRoles

TENANT_ROLE_OWNER = MembershipRoles.OWNER.value
TENANT_ROLE_CREATOR = MembershipRoles.CREATOR.value
TENANT_ROLE_ADMIN = MembershipRoles.ADMIN.value
TENANT_ROLE_MEMBER = MembershipRoles.MEMBER.value

_ROLE_CHOICES = [(role.value, role.name.title()) for role in MembershipRoles]


class TenantModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=100, unique=True)
    vat = models.IntegerField(unique=True, null=True, blank=True)
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
            models.Index(fields=["vat"]),
        ]

    def __str__(self) -> str:
        return self.slug


class TenantMembershipModel(models.Model):
    """
    Tabla intermedia explícita tenant ↔ user.
    Registra quién invitó a quién, cuándo entró y cuándo salió.
    """

    id = models.BigAutoField(primary_key=True)
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
