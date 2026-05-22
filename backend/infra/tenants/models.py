from django.db import models

from infra.authz.models import AuthUserModel
from infra.common.classes import ROLE_CHOICES


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
        db_table = "tenants_Tenant"
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
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
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
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
        db_table = "tenants_TenantMembership"
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"
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


class OrganizationProfileModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.OneToOneField(
        TenantModel,
        on_delete=models.CASCADE,
        related_name="organization_profile",
    )
    public_name = models.CharField(max_length=200, blank=True, default="")
    legal_name = models.CharField(max_length=200, blank=True, default="")
    country = models.CharField(max_length=2, blank=True, default="")
    timezone = models.CharField(max_length=64, blank=True, default="UTC")
    currency = models.CharField(max_length=3, default="EUR")
    vat_number = models.CharField(max_length=32, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenants_OrganizationProfile"
        verbose_name = "Organisation profile"
        verbose_name_plural = "Organisation profiles"
        indexes = [
            models.Index(fields=["tenant"]),
        ]

    def __str__(self) -> str:
        return f"OrgProfile<{self.tenant_id}>"
