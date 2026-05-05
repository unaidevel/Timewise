from infra.common.exceptions import Conflict, NotFound
from infra.tenants.decorators import only_admin
from infra.tenants.dtos.dtos import (
    AddMemberRequest,
    TenantMemberResponse,
    TenantOut,
    TenantUpdate,
)
from infra.tenants.entities.tenant_entities import (
    TenantEntity,
    TenantMemberEntity,
    TenantMembershipEntity,
    TenantUpdateEntity,
)
from infra.tenants.repositories.tenants_repository import TenantRepository


class TenantService:
    @staticmethod
    def create(entity: TenantEntity, created_by_id: int) -> TenantOut:
        if TenantRepository.find_by_slug(entity.slug):
            raise Conflict(f"A tenant with slug '{entity.slug}' already exists.")
        return TenantRepository.create(entity, created_by_id)

    @staticmethod
    @only_admin
    def update_tenant(payload: TenantUpdate, user_id: int) -> TenantOut:
        entity = TenantUpdateEntity(**payload.model_dump())
        if entity.slug is not None:
            existing = TenantService.tenant_exists_by_slug(entity.slug)
            if existing:
                raise Conflict(f"A tenant with slug '{entity.slug}' already exists.")
        tenant = TenantService.get_by_id(entity.tenant_id, user_id)
        return TenantRepository.update_tenant(entity, tenant.id)

    @staticmethod
    def add_membership(
        tenant_id: int,
        user_id: int,
        entity: TenantMembershipEntity,
        invited_by_id: int | None,
    ) -> TenantMemberResponse:
        return TenantRepository.add_membership(
            tenant_id, user_id, entity, invited_by_id
        )

    @staticmethod
    @only_admin
    def get_by_id(tenant_id: int, user_id: int) -> TenantOut:
        tenant = TenantRepository.get_by_id(tenant_id)
        if not tenant:
            raise NotFound(f"Tenant {tenant_id} not found.")
        return tenant

    @staticmethod
    def add_member(
        tenant_id: int,
        payload: AddMemberRequest,
        invited_by_id: int,
    ) -> TenantMemberResponse:
        entity = TenantMemberEntity(**payload.model_dump())
        tenant = TenantRepository.get_by_id(tenant_id)
        if not tenant:
            raise NotFound(f"Tenant {tenant_id} not found.")

        existing = TenantRepository.find_active_membership(tenant_id, entity.user_id)
        if existing:
            raise Conflict("User is already an active member.")

        return TenantRepository.add_membership(
            tenant_id,
            entity.user_id,
            TenantMembershipEntity(role=entity.role),
            invited_by_id,
        )

    @staticmethod
    def list_members(tenant_id: int) -> list[TenantMemberResponse]:
        tenant = TenantRepository.get_by_id(tenant_id)
        if not tenant:
            raise NotFound(f"Tenant {tenant_id} not found.")
        return TenantRepository.list_memberships(tenant_id)

    @staticmethod
    def remove_member(
        tenant_id: int,
        membership_id: int,
        reason: str,
    ) -> TenantMemberResponse:
        tenant = TenantRepository.get_by_id(tenant_id)
        if not tenant:
            raise NotFound(f"Tenant {tenant_id} not found.")
        membership = TenantRepository.remove_membership(membership_id, reason)
        if not membership:
            raise NotFound("Membership not found or already inactive.")
        return membership

    @staticmethod
    def tenant_exists_by_slug(slug: str) -> bool:
        return TenantRepository.tenant_exists_by_slug(slug)
