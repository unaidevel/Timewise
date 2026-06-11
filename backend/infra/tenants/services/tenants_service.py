from django.utils import timezone

from infra.common.exceptions import Conflict, NotFound
from infra.tenants.decorators import any_employee, only_admin
from infra.tenants.dtos.dtos import (
    AddMemberRequest,
    OrganizationProfileIn,
    OrganizationProfileOut,
    TenantMemberResponse,
    TenantOut,
    TenantUpdate,
)
from infra.tenants.entities.tenant_entities import (
    OrganizationProfileUpdateEntity,
    TenantEntity,
    TenantMemberEntity,
    TenantMembershipEntity,
    TenantUpdateEntity,
)
from infra.tenants.repositories.tenants_repository import (
    OrganizationProfileRepository,
    TenantRepository,
)


class TenantService:
    @staticmethod
    def create(entity: TenantEntity, user_id: int) -> TenantOut:
        if TenantRepository.find_by_slug(entity.slug):
            raise Conflict(f"A tenant with slug '{entity.slug}' already exists.")
        return TenantRepository.create(entity, user_id)

    @staticmethod
    @only_admin
    def update_tenant(payload: TenantUpdate, user_id: int) -> TenantOut:
        entity = TenantUpdateEntity(**payload.model_dump())
        TenantService.get_by_id(entity.tenant_id, user_id)
        return TenantRepository.update_tenant(entity)

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
    def list_for_user(user_id: int) -> list[TenantOut]:
        return TenantRepository.list_for_user(user_id)

    @staticmethod
    @only_admin
    def add_member(
        tenant_id: int,
        payload: AddMemberRequest,
        user_id: int,
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
            user_id,
        )

    @staticmethod
    @any_employee
    def list_members(tenant_id: int, user_id: int) -> list[TenantMemberResponse]:
        tenant = TenantRepository.get_by_id(tenant_id)
        if not tenant:
            raise NotFound(f"Tenant {tenant_id} not found.")
        return TenantRepository.list_memberships(tenant_id)

    @staticmethod
    @only_admin
    def remove_member(
        tenant_id: int,
        membership_id: int,
        reason: str,
        user_id: int,
    ) -> TenantMemberResponse:
        tenant = TenantRepository.get_by_id(tenant_id)
        if not tenant:
            raise NotFound(f"Tenant {tenant_id} not found.")
        membership = TenantRepository.remove_membership(
            membership_id, reason, left_at=timezone.now()
        )
        if not membership:
            raise NotFound("Membership not found or already inactive.")
        return membership

    @staticmethod
    def tenant_exists_by_slug(slug: str) -> bool:
        return TenantRepository.tenant_exists_by_slug(slug)


class OrganizationProfileService:
    @staticmethod
    def create_default(tenant_id: int) -> OrganizationProfileOut:
        return OrganizationProfileRepository.create_default(tenant_id)

    @staticmethod
    @any_employee
    def get(tenant_id: int, user_id: int) -> OrganizationProfileOut:
        profile = OrganizationProfileRepository.get_by_tenant(tenant_id)
        if not profile:
            raise NotFound(f"Organization profile for tenant {tenant_id} not found.")
        return profile

    @staticmethod
    @only_admin
    def update(
        tenant_id: int, payload: OrganizationProfileIn, user_id: int
    ) -> OrganizationProfileOut:
        entity = OrganizationProfileUpdateEntity(**payload.model_dump())
        updated = OrganizationProfileRepository.update(tenant_id, entity)
        if not updated:
            raise NotFound(f"Organization profile for tenant {tenant_id} not found.")
        return updated
