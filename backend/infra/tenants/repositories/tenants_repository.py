from datetime import datetime

from infra.tenants.dtos.dtos import (
    OrganizationProfileOut,
    TenantMemberResponse,
    TenantOut,
)
from infra.tenants.entities.tenant_entities import (
    OrganizationProfileUpdateEntity,
    TenantEntity,
    TenantMembershipEntity,
    TenantUpdateEntity,
)
from infra.tenants.models import (
    OrganizationProfileModel,
    TenantMembershipModel,
    TenantModel,
)


class TenantRepository:
    @staticmethod
    def create(entity: TenantEntity, user_id: int) -> TenantOut:
        if not isinstance(entity, TenantEntity):
            raise TypeError(f"Expected TenantEntity, got {type(entity).__name__}")
        model = TenantModel.objects.create(
            name=entity.name,
            slug=entity.slug,
            created_by_id=user_id,
        )
        return TenantOut.model_validate(model)

    @staticmethod
    def update_tenant(entity: TenantUpdateEntity) -> TenantOut:
        if not isinstance(entity, TenantUpdateEntity):
            raise TypeError(f"Expected TenantUpdateEntity, got {type(entity).__name__}")
        tenant = TenantModel(
            id=entity.tenant_id,
            name=entity.name,
            slug=entity.slug,
            is_active=entity.is_active,
        )
        tenant.save(update_fields=["name", "slug", "is_active", "updated_at"])
        return TenantOut.model_validate(tenant)

    @staticmethod
    def get_by_id(tenant_id: int) -> TenantOut | None:
        model = TenantModel.objects.filter(id=tenant_id).first()
        return TenantOut.model_validate(model) if model else None

    @staticmethod
    def find_by_slug(slug: str) -> TenantOut | None:
        model = TenantModel.objects.filter(slug=slug).first()
        return TenantOut.model_validate(model) if model else None

    @staticmethod
    def list_for_user(user_id: int) -> list[TenantOut]:
        return [
            TenantOut.model_validate(t)
            for t in TenantModel.objects.filter(
                memberships__user_id=user_id,
                memberships__left_at__isnull=True,
            )
            .distinct()
            .order_by("name")
        ]

    @staticmethod
    def add_membership(
        tenant_id: int,
        user_id: int,
        entity: TenantMembershipEntity,
        invited_by_id: int | None,
    ) -> TenantMemberResponse:
        if not isinstance(entity, TenantMembershipEntity):
            raise TypeError(
                f"Expected TenantMembershipEntity, got {type(entity).__name__}"
            )
        model = TenantMembershipModel.objects.create(
            tenant_id=tenant_id,
            user_id=user_id,
            role=entity.role,
            invited_by_id=invited_by_id,
        )
        return TenantMemberResponse.model_validate(model)

    @staticmethod
    def find_active_membership(
        tenant_id: int, user_id: int
    ) -> TenantMemberResponse | None:
        model = TenantMembershipModel.objects.filter(
            tenant_id=tenant_id,
            user_id=user_id,
            left_at__isnull=True,
        ).first()
        return TenantMemberResponse.model_validate(model) if model else None

    @staticmethod
    def list_memberships(tenant_id: int) -> list[TenantMemberResponse]:
        return [
            TenantMemberResponse.model_validate(m)
            for m in TenantMembershipModel.objects.filter(tenant_id=tenant_id).order_by(
                "joined_at"
            )
        ]

    @staticmethod
    def remove_membership(
        membership_id: int, reason: str, left_at: datetime
    ) -> TenantMemberResponse | None:
        rows = TenantMembershipModel.objects.filter(
            id=membership_id,
            left_at__isnull=True,
        ).update(left_at=left_at, left_reason=reason)
        if rows == 0:
            return None
        model = TenantMembershipModel.objects.get(id=membership_id)
        return TenantMemberResponse.model_validate(model)

    @staticmethod
    def tenant_exists_by_slug(slug: str) -> bool:
        return TenantModel.objects.filter(slug=slug).exists()


class OrganizationProfileRepository:
    @staticmethod
    def create_default(tenant_id: int) -> OrganizationProfileOut:
        model = OrganizationProfileModel.objects.create(tenant_id=tenant_id)
        return OrganizationProfileOut.model_validate(model)

    @staticmethod
    def get_by_tenant(tenant_id: int) -> OrganizationProfileOut | None:
        model = OrganizationProfileModel.objects.filter(tenant_id=tenant_id).first()
        return OrganizationProfileOut.model_validate(model) if model else None

    @staticmethod
    def update(
        tenant_id: int, entity: OrganizationProfileUpdateEntity
    ) -> OrganizationProfileOut | None:
        if not isinstance(entity, OrganizationProfileUpdateEntity):
            raise TypeError(
                f"Expected OrganizationProfileUpdateEntity, got {type(entity).__name__}"
            )
        rows = OrganizationProfileModel.objects.filter(tenant_id=tenant_id).update(
            public_name=entity.public_name,
            legal_name=entity.legal_name,
            workspace_name=entity.workspace_name,
            country=entity.country,
            timezone=entity.timezone,
            currency=entity.currency,
            fiscal_year_start=entity.fiscal_year_start,
            vat_number=entity.vat_number,
            default_locale=entity.default_locale,
        )
        if rows == 0:
            return None
        model = OrganizationProfileModel.objects.get(tenant_id=tenant_id)
        return OrganizationProfileOut.model_validate(model)
