from uuid import UUID

from infra.tenants.dtos.tenant_dtos import Tenant, TenantMembership
from infra.tenants.entities.tenant_entities import TenantName, TenantSlug
from infra.tenants.exceptions import (
    MemberAlreadyExistsError,
    MemberNotFoundError,
    TenantAlreadyExistsError,
    TenantNotFoundError,
)
from infra.tenants.models import TENANT_ROLE_OWNER
from infra.tenants.repositories.tenants_repository import TenantRepository


class TenantService:
    @staticmethod
    def create(name: str, slug: str, created_by_id: UUID) -> Tenant:
        tenant_name = TenantName(name)
        tenant_slug = TenantSlug(slug)

        if TenantRepository.find_by_slug(tenant_slug.value):
            raise TenantAlreadyExistsError(
                f"A tenant with slug '{tenant_slug.value}' already exists."
            )

        tenant = TenantRepository.create(
            name=tenant_name.value,
            slug=tenant_slug.value,
            created_by_id=created_by_id,
        )
        TenantRepository.add_membership(
            tenant_id=tenant.id,
            user_id=created_by_id,
            role=TENANT_ROLE_OWNER,
            invited_by_id=None,
        )
        return tenant

    @staticmethod
    def get_by_id(tenant_id: UUID) -> Tenant:
        tenant = TenantRepository.find_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found.")
        return tenant

    @staticmethod
    def list_all() -> list[Tenant]:
        return TenantRepository.list_all()

    @staticmethod
    def add_member(
        tenant_id: UUID,
        user_id: UUID,
        role: str,
        invited_by_id: UUID,
    ) -> TenantMembership:
        tenant = TenantRepository.find_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found.")

        existing = TenantRepository.find_active_membership(tenant_id, user_id)
        if existing:
            raise MemberAlreadyExistsError("User is already an active member.")

        return TenantRepository.add_membership(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            invited_by_id=invited_by_id,
        )

    @staticmethod
    def list_members(tenant_id: UUID) -> list[TenantMembership]:
        tenant = TenantRepository.find_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found.")
        return TenantRepository.list_memberships(tenant_id)

    @staticmethod
    def remove_member(
        tenant_id: UUID,
        membership_id: UUID,
        reason: str,
    ) -> TenantMembership:
        tenant = TenantRepository.find_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found.")
        return TenantRepository.remove_membership(membership_id, reason)
