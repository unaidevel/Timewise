from infra.tenants.dtos.dtos import TenantIn
from infra.tenants.dtos.tenant_dtos import Tenant, TenantMembership
from infra.tenants.entities.tenant_entities import TenantEntity
from infra.tenants.exceptions import (
    MemberAlreadyExistsError,
    TenantAlreadyExistsError,
    TenantNotFoundError,
)
from infra.tenants.models import TENANT_ROLE_OWNER
from infra.tenants.repositories.tenants_repository import TenantRepository
from django.db import transaction


class TenantService:
    @staticmethod
    def create(payload: TenantIn, created_by_id: int) -> Tenant:
        tenant = TenantEntity(**payload.model_dump())

        if TenantRepository.find_by_slug(tenant.slug):
            raise TenantAlreadyExistsError(
                f"A tenant with slug '{tenant.slug}' already exists."
            )

        with transaction.atomic():
            created_tenant = TenantRepository.create(
                name=tenant.name,
                slug=tenant.slug,
                created_by_id=created_by_id,
            )
            TenantRepository.add_membership(
                tenant_id=created_tenant.id,
                user_id=created_by_id,
                role=TENANT_ROLE_OWNER,
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
        user_id: int,
        role: str,
        invited_by_id: int,
    ) -> TenantMembership:
        tenant = TenantRepository.get_by_id(tenant_id)
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
        return TenantRepository.remove_membership(membership_id, reason)
