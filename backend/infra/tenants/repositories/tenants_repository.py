from uuid import UUID

from django.db import IntegrityError
from django.utils import timezone

from infra.tenants.dtos.mappers.tenant_mapper import to_tenant, to_tenant_membership
from infra.tenants.dtos.tenant_dtos import Tenant, TenantMembership
from infra.tenants.exceptions import MemberAlreadyExistsError, MemberNotFoundError, TenantAlreadyExistsError
from infra.tenants.models import TenantMembershipModel, TenantModel


class TenantRepository:
    @staticmethod
    def create(name: str, slug: str, created_by_id: UUID) -> Tenant:
        try:
            model = TenantModel.objects.create(
                name=name,
                slug=slug,
                created_by_id=created_by_id,
            )
        except IntegrityError as exc:
            raise TenantAlreadyExistsError(
                f"A tenant with slug '{slug}' already exists."
            ) from exc
        return to_tenant(model)

    @staticmethod
    def find_by_id(tenant_id: UUID) -> Tenant | None:
        model = TenantModel.objects.filter(id=tenant_id).first()
        return to_tenant(model) if model else None

    @staticmethod
    def find_by_slug(slug: str) -> Tenant | None:
        model = TenantModel.objects.filter(slug=slug).first()
        return to_tenant(model) if model else None

    @staticmethod
    def list_all() -> list[Tenant]:
        return [to_tenant(m) for m in TenantModel.objects.all().order_by("name")]

    @staticmethod
    def add_membership(
        tenant_id: UUID,
        user_id: UUID,
        role: str,
        invited_by_id: UUID | None,
    ) -> TenantMembership:
        try:
            model = TenantMembershipModel.objects.create(
                tenant_id=tenant_id,
                user_id=user_id,
                role=role,
                invited_by_id=invited_by_id,
            )
        except IntegrityError as exc:
            raise MemberAlreadyExistsError(
                "User is already an active member of this tenant."
            ) from exc
        return to_tenant_membership(model)

    @staticmethod
    def find_active_membership(tenant_id: UUID, user_id: UUID) -> TenantMembership | None:
        model = TenantMembershipModel.objects.filter(
            tenant_id=tenant_id,
            user_id=user_id,
            left_at__isnull=True,
        ).first()
        return to_tenant_membership(model) if model else None

    @staticmethod
    def list_memberships(tenant_id: UUID) -> list[TenantMembership]:
        return [
            to_tenant_membership(m)
            for m in TenantMembershipModel.objects.filter(
                tenant_id=tenant_id
            ).order_by("joined_at")
        ]

    @staticmethod
    def remove_membership(membership_id: UUID, reason: str) -> TenantMembership:
        rows = TenantMembershipModel.objects.filter(
            id=membership_id,
            left_at__isnull=True,
        ).update(left_at=timezone.now(), left_reason=reason)
        if rows == 0:
            raise MemberNotFoundError("Membership not found or already inactive.")
        model = TenantMembershipModel.objects.get(id=membership_id)
        return to_tenant_membership(model)
