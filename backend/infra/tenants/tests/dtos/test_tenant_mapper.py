from django.test import TestCase
from django.utils import timezone

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.tenants.dtos.mappers.tenant_mapper import to_tenant, to_tenant_membership
from infra.tenants.models import TenantMembershipModel, TenantModel


def make_user(email: str = "owner@example.com"):
    return AuthRepository.create_user(
        email=email,
        full_name="Test User",
        password_hash=AuthService._hash_password("SecurePass123!"),
    )


class TenantMapperTests(TestCase):
    def test_to_tenant_maps_model_fields(self):
        owner = make_user()
        model = TenantModel.objects.create(
            name="Acme Corp",
            slug="acme",
            created_by_id=owner.id,
        )

        tenant = to_tenant(model)

        assert tenant.id == model.id
        assert tenant.name == "Acme Corp"
        assert tenant.slug == "acme"
        assert tenant.is_active is True
        assert tenant.created_at == model.created_at
        assert tenant.updated_at == model.updated_at
        assert tenant.created_by_id == owner.id

    def test_to_tenant_membership_maps_empty_reason_to_none(self):
        owner = make_user()
        member = make_user("member@example.com")
        tenant = TenantModel.objects.create(
            name="Acme Corp",
            slug="acme",
            created_by_id=owner.id,
        )
        model = TenantMembershipModel.objects.create(
            tenant_id=tenant.id,
            user_id=member.id,
            role=MembershipRoles.MEMBER.value,
            invited_by_id=owner.id,
        )

        membership = to_tenant_membership(model)

        assert membership.id == model.id
        assert membership.tenant_id == tenant.id
        assert membership.user_id == member.id
        assert membership.role == MembershipRoles.MEMBER.value
        assert membership.joined_at == model.joined_at
        assert membership.invited_by_id == owner.id
        assert membership.left_at is None
        assert membership.left_reason is None

    def test_to_tenant_membership_preserves_left_reason(self):
        owner = make_user()
        member = make_user("member@example.com")
        tenant = TenantModel.objects.create(
            name="Acme Corp",
            slug="acme",
            created_by_id=owner.id,
        )
        left_at = timezone.now()
        model = TenantMembershipModel.objects.create(
            tenant_id=tenant.id,
            user_id=member.id,
            role=MembershipRoles.ADMIN.value,
            invited_by_id=owner.id,
            left_at=left_at,
            left_reason="Resigned",
        )

        membership = to_tenant_membership(model)

        assert membership.left_at == left_at
        assert membership.left_reason == "Resigned"
