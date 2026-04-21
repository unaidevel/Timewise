from django.utils import timezone

from infra.tenants.dtos.dtos import TenantMemberResponse, TenantOut
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.models import TenantMembershipModel, TenantModel


class TenantRepository:
    @staticmethod
    def create(entity: TenantEntity, created_by_id: int) -> TenantOut:
        if not isinstance(entity, TenantEntity):
            raise TypeError(f"Expected TenantEntity, got {type(entity).__name__}")
        model = TenantModel.objects.create(
            name=entity.name,
            slug=entity.slug,
            created_by_id=created_by_id,
        )
        return TenantOut.model_validate(model)

    @staticmethod
    def get_by_id(tenant_id: int) -> TenantOut | None:
        model = TenantModel.objects.filter(id=tenant_id).first()
        return TenantOut.model_validate(model) if model else None

    @staticmethod
    def find_by_slug(slug: str) -> TenantOut | None:
        model = TenantModel.objects.filter(slug=slug).first()
        return TenantOut.model_validate(model) if model else None

    @staticmethod
    def list_all() -> list[TenantOut]:
        return [
            TenantOut.model_validate(m)
            for m in TenantModel.objects.all().order_by("name")
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
        membership_id: int, reason: str
    ) -> TenantMemberResponse | None:
        rows = TenantMembershipModel.objects.filter(
            id=membership_id,
            left_at__isnull=True,
        ).update(left_at=timezone.now(), left_reason=reason)
        if rows == 0:
            return None
        model = TenantMembershipModel.objects.get(id=membership_id)
        return TenantMemberResponse.model_validate(model)
