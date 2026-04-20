from django.db import transaction

from infra.common.classes import MembershipRoles
from infra.tenants.dtos.dtos import AddMemberRequest, TenantIn
from infra.tenants.dtos.tenant_dtos import Tenant, TenantMembership
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.exceptions import (
    MemberAlreadyExistsError,
    MemberNotFoundError,
    TenantAlreadyExistsError,
    TenantNotFoundError,
)
from infra.tenants.repositories.tenants_repository import TenantRepository


class TenantService:
    @staticmethod
    def create(payload: TenantIn, created_by_id: int) -> Tenant:
        entity = TenantEntity(**payload.model_dump())

        if TenantRepository.find_by_slug(entity.slug):
            raise TenantAlreadyExistsError(
                f"A tenant with slug '{entity.slug}' already exists."
            )

        with transaction.atomic():
            created_tenant = TenantRepository.create(entity, created_by_id)
            TenantRepository.add_membership(
                tenant_id=created_tenant.id,
                user_id=created_by_id,
                entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
                invited_by_id=None,
            )
        return created_tenant

    @staticmethod
    def get_by_id(tenant_id: int) -> Tenant:
        tenant = TenantRepository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found.")
        return tenant

    @staticmethod
    def list_all() -> list[Tenant]:
        return TenantRepository.list_all()

    @staticmethod
    def add_member(
        tenant_id: int,
        payload: AddMemberRequest,
        invited_by_id: int,
    ) -> TenantMembership:
        tenant = TenantRepository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found.")

        existing = TenantRepository.find_active_membership(tenant_id, payload.user_id)
        if existing:
            raise MemberAlreadyExistsError("User is already an active member.")

        entity = TenantMembershipEntity(role=payload.role)
        return TenantRepository.add_membership(
            tenant_id,
            payload.user_id,
            entity,
            invited_by_id,
        )

    @staticmethod
    def list_members(tenant_id: int) -> list[TenantMembership]:
        tenant = TenantRepository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found.")
        return TenantRepository.list_memberships(tenant_id)

    @staticmethod
    def remove_member(
        tenant_id: int,
        membership_id: int,
        reason: str,
    ) -> TenantMembership:
        tenant = TenantRepository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found.")
        membership = TenantRepository.remove_membership(membership_id, reason)
        if not membership:
            raise MemberNotFoundError("Membership not found or already inactive.")
        return membership
