from django.db import transaction

from infra.common.classes import MembershipRoles
from infra.tenants.dtos.dtos import TenantIn, TenantOut
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.services.tenants_service import TenantService
from product.workforce.services.workforce_service import WorkforceService


class TenantOrchestrator:
    @staticmethod
    def create(payload: TenantIn, created_by_id: int) -> TenantOut:
        entity = TenantEntity(**payload.model_dump())

        with transaction.atomic():
            created_tenant = TenantService.create(entity, created_by_id)
            TenantService.add_membership(
                tenant_id=created_tenant.id,
                user_id=created_by_id,
                entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
                invited_by_id=None,
            )
            WorkforceService.create_default_roles(created_tenant.id)

        return created_tenant
