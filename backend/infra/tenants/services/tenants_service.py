from django.db import transaction

from infra.common.classes import MembershipRoles
from infra.tenants.dtos.dtos import (
    AddMemberRequest,
    TenantIn,
    TenantMemberResponse,
    TenantOut,
)
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
    def create(entity: TenantEntity, created_by_id: int) -> TenantOut:
        return TenantRepository.create(entity, created_by_id)
    @staticmethod
    def get_by_id(tenant_id: int) -> TenantOut:
        tenant = TenantRepository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found.")
        return tenant

    @staticmethod
    def get_by_slug(slug: str) -> TenantOut:
        tenant = TenantRepository.find_by_slug(slug)
        if not tenant:
            raise TenantNotFoundError(f"Tenant with slug '{slug}' not found.")
        return tenant
    
    @staticmethod
    def list_all() -> list[TenantOut]:
        return TenantRepository.list_all()

    @staticmethod
    def add_member(
        tenant_id: int,
        payload: AddMemberRequest,
        invited_by_id: int,
    ) -> TenantMemberResponse:
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
    def list_members(tenant_id: int) -> list[TenantMemberResponse]:
        tenant = TenantRepository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found.")
        return TenantRepository.list_memberships(tenant_id)

    @staticmethod
    def remove_member(
        tenant_id: int,
        membership_id: int,
        reason: str,
    ) -> TenantMemberResponse:
        tenant = TenantRepository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found.")
        membership = TenantRepository.remove_membership(membership_id, reason)
        if not membership:
            raise MemberNotFoundError("Membership not found or already inactive.")
        return membership

    def add_membership(tenant_id=created_tenant.id,
                user_id=created_by_id,
                entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
                invited_by_id=None,) -> TenantMemberResponse:
        return TenantRepository.add_membership(
            tenant_id=tenant_id,
            user_id=user_id,
            entity=entity,
            invited_by_id=invited_by_id,
        )