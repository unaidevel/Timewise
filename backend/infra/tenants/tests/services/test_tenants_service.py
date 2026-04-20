import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.tenants.dtos.dtos import AddMemberRequest, TenantIn
from infra.tenants.exceptions import (
    InvalidMemberRoleError,
    InvalidTenantNameError,
    InvalidTenantSlugError,
    MemberAlreadyExistsError,
    MemberNotFoundError,
    TenantAlreadyExistsError,
    TenantNotFoundError,
)
from infra.tenants.models import TenantMembershipModel
from infra.tenants.services.tenants_service import TenantService


def make_user(email: str = "owner@example.com"):
    return AuthRepository.create_user(
        email=email,
        full_name="Test User",
        password_hash=AuthService._hash_password("SecurePass123!"),
    )


class TenantServiceTests(TestCase):
    def test_create_normalizes_values_and_adds_owner_membership(self):
        owner = make_user()

        tenant = TenantService.create(
            TenantIn(name="  Acme Corp  ", slug="  Acme-Corp  "),
            created_by_id=owner.id,
        )

        assert tenant.name == "Acme Corp"
        assert tenant.slug == "acme-corp"
        assert tenant.created_by_id == owner.id

        memberships = TenantMembershipModel.objects.filter(tenant_id=tenant.id)
        assert memberships.count() == 1

        membership = memberships.get()
        assert membership.user_id == owner.id
        assert membership.role == MembershipRoles.OWNER.value
        assert membership.invited_by_id is None
        assert membership.left_at is None

    def test_create_raises_if_slug_already_exists(self):
        owner = make_user()
        TenantService.create(
            TenantIn(name="Acme Corp", slug="acme"),
            created_by_id=owner.id,
        )

        with pytest.raises(TenantAlreadyExistsError, match="slug 'acme'"):
            TenantService.create(
                TenantIn(name="Another Acme", slug="  ACME  "),
                created_by_id=owner.id,
            )

    def test_create_raises_on_invalid_name(self):
        owner = make_user()

        with pytest.raises(InvalidTenantNameError):
            TenantService.create(
                TenantIn(name="   ", slug="acme"), created_by_id=owner.id
            )

    def test_create_raises_on_invalid_slug(self):
        owner = make_user()

        with pytest.raises(InvalidTenantSlugError):
            TenantService.create(
                TenantIn(name="Acme Corp", slug="-invalid"),
                created_by_id=owner.id,
            )

    def test_get_by_id_returns_tenant(self):
        owner = make_user()
        created = TenantService.create(
            TenantIn(name="Acme Corp", slug="acme"),
            created_by_id=owner.id,
        )

        found = TenantService.get_by_id(created.id)

        assert found == created

    def test_get_by_id_raises_if_not_found(self):
        with pytest.raises(TenantNotFoundError, match="Tenant 999 not found"):
            TenantService.get_by_id(999)

    def test_list_all_returns_all_tenants_in_name_order(self):
        owner = make_user()
        TenantService.create(TenantIn(name="Zulu", slug="zulu"), created_by_id=owner.id)
        TenantService.create(
            TenantIn(name="Alpha", slug="alpha"),
            created_by_id=owner.id,
        )

        tenants = TenantService.list_all()

        assert [tenant.name for tenant in tenants] == ["Alpha", "Zulu"]

    def test_add_member_creates_membership(self):
        owner = make_user()
        member = make_user("member@example.com")
        tenant = TenantService.create(
            TenantIn(name="Acme Corp", slug="acme"),
            created_by_id=owner.id,
        )

        membership = TenantService.add_member(
            tenant_id=tenant.id,
            payload=AddMemberRequest(
                user_id=member.id,
                role=MembershipRoles.MEMBER.value,
            ),
            invited_by_id=owner.id,
        )

        assert membership.tenant_id == tenant.id
        assert membership.user_id == member.id
        assert membership.role == MembershipRoles.MEMBER.value
        assert membership.invited_by_id == owner.id
        assert membership.left_at is None

    def test_add_member_raises_if_tenant_not_found(self):
        owner = make_user()
        member = make_user("member@example.com")

        with pytest.raises(TenantNotFoundError, match="Tenant 999 not found"):
            TenantService.add_member(
                tenant_id=999,
                payload=AddMemberRequest(
                    user_id=member.id,
                    role=MembershipRoles.MEMBER.value,
                ),
                invited_by_id=owner.id,
            )

    def test_add_member_raises_if_already_member(self):
        owner = make_user()
        member = make_user("member@example.com")
        tenant = TenantService.create(
            TenantIn(name="Acme Corp", slug="acme"),
            created_by_id=owner.id,
        )
        TenantService.add_member(
            tenant_id=tenant.id,
            payload=AddMemberRequest(
                user_id=member.id,
                role=MembershipRoles.MEMBER.value,
            ),
            invited_by_id=owner.id,
        )

        with pytest.raises(MemberAlreadyExistsError):
            TenantService.add_member(
                tenant_id=tenant.id,
                payload=AddMemberRequest(
                    user_id=member.id,
                    role=MembershipRoles.ADMIN.value,
                ),
                invited_by_id=owner.id,
            )

    def test_add_member_raises_on_invalid_role(self):
        owner = make_user()
        member = make_user("member@example.com")
        tenant = TenantService.create(
            TenantIn(name="Acme Corp", slug="acme"),
            created_by_id=owner.id,
        )
        payload = AddMemberRequest.model_construct(
            user_id=member.id,
            role="invalid-role",
        )

        with pytest.raises(InvalidMemberRoleError, match="Invalid role"):
            TenantService.add_member(
                tenant_id=tenant.id,
                payload=payload,
                invited_by_id=owner.id,
            )

    def test_list_members_returns_memberships(self):
        owner = make_user()
        member = make_user("member@example.com")
        tenant = TenantService.create(
            TenantIn(name="Acme Corp", slug="acme"),
            created_by_id=owner.id,
        )
        TenantService.add_member(
            tenant_id=tenant.id,
            payload=AddMemberRequest(
                user_id=member.id,
                role=MembershipRoles.MEMBER.value,
            ),
            invited_by_id=owner.id,
        )

        memberships = TenantService.list_members(tenant.id)

        assert len(memberships) == 2
        assert [membership.user_id for membership in memberships] == [
            owner.id,
            member.id,
        ]

    def test_list_members_raises_if_tenant_not_found(self):
        with pytest.raises(TenantNotFoundError, match="Tenant 999 not found"):
            TenantService.list_members(999)

    def test_remove_member_marks_membership_inactive(self):
        owner = make_user()
        member = make_user("member@example.com")
        tenant = TenantService.create(
            TenantIn(name="Acme Corp", slug="acme"),
            created_by_id=owner.id,
        )
        membership = TenantService.add_member(
            tenant_id=tenant.id,
            payload=AddMemberRequest(
                user_id=member.id,
                role=MembershipRoles.MEMBER.value,
            ),
            invited_by_id=owner.id,
        )

        removed = TenantService.remove_member(
            tenant_id=tenant.id,
            membership_id=membership.id,
            reason="Left the company",
        )

        assert removed.id == membership.id
        assert removed.left_at is not None
        assert removed.left_reason == "Left the company"
        stored = TenantMembershipModel.objects.get(id=membership.id)
        assert stored.left_at is not None
        assert stored.left_reason == "Left the company"

    def test_remove_member_raises_if_tenant_not_found(self):
        with pytest.raises(TenantNotFoundError, match="Tenant 999 not found"):
            TenantService.remove_member(
                tenant_id=999,
                membership_id=1,
                reason="",
            )

    def test_remove_member_raises_if_membership_not_found(self):
        owner = make_user()
        tenant = TenantService.create(
            TenantIn(name="Acme Corp", slug="acme"),
            created_by_id=owner.id,
        )

        with pytest.raises(
            MemberNotFoundError,
            match="Membership not found or already inactive",
        ):
            TenantService.remove_member(
                tenant_id=tenant.id,
                membership_id=999,
                reason="",
            )
