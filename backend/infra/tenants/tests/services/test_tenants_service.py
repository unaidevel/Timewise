import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.tenants.dtos.dtos import AddMemberRequest, TenantMemberResponse, TenantOut
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.exceptions import (
    InvalidMemberRoleError,
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


def make_tenant(user_id: int, slug: str = "acme") -> TenantOut:
    return TenantService.create(
        TenantEntity(name="Acme Corp", slug=slug), created_by_id=user_id
    )


class TenantServiceCreateTests(TestCase):
    def test_create_returns_persisted_tenant(self):
        owner = make_user()

        tenant = TenantService.create(
            TenantEntity(name="Acme Corp", slug="acme"), created_by_id=owner.id
        )

        assert tenant.name == "Acme Corp"
        assert tenant.slug == "acme"
        assert tenant.created_by_id == owner.id
        assert isinstance(tenant, TenantOut)

    def test_create_does_not_create_membership(self):
        owner = make_user()

        TenantService.create(
            TenantEntity(name="Acme Corp", slug="acme"), created_by_id=owner.id
        )

        assert TenantMembershipModel.objects.count() == 0

    def test_create_raises_if_slug_already_exists(self):
        owner = make_user()
        TenantService.create(TenantEntity(name="Acme Corp", slug="acme"), created_by_id=owner.id)

        with pytest.raises(TenantAlreadyExistsError, match="slug 'acme'"):
            TenantService.create(
                TenantEntity(name="Another Acme", slug="acme"), created_by_id=owner.id
            )


class TenantServiceAddMembershipTests(TestCase):
    def test_add_membership_creates_record(self):
        owner = make_user()
        tenant = make_tenant(owner.id)

        membership = TenantService.add_membership(
            tenant_id=tenant.id,
            user_id=owner.id,
            entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
            invited_by_id=None,
        )

        assert isinstance(membership, TenantMemberResponse)
        assert membership.tenant_id == tenant.id
        assert membership.user_id == owner.id
        assert membership.role == MembershipRoles.OWNER.value
        assert membership.invited_by_id is None
        assert membership.left_at is None


class TenantServiceGetTests(TestCase):
    def test_get_by_id_returns_tenant(self):
        owner = make_user()
        created = make_tenant(owner.id)

        found = TenantService.get_by_id(created.id)

        assert found == created

    def test_get_by_id_raises_if_not_found(self):
        with pytest.raises(TenantNotFoundError, match="Tenant 999 not found"):
            TenantService.get_by_id(999)

    def test_list_all_returns_all_tenants_in_name_order(self):
        owner = make_user()
        TenantService.create(TenantEntity(name="Zulu", slug="zulu"), created_by_id=owner.id)
        TenantService.create(TenantEntity(name="Alpha", slug="alpha"), created_by_id=owner.id)

        tenants = TenantService.list_all()

        assert [t.name for t in tenants] == ["Alpha", "Zulu"]


class TenantServiceMemberTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.tenant = make_tenant(self.owner.id)

    def test_add_member_creates_membership(self):
        member = make_user("member@example.com")

        membership = TenantService.add_member(
            tenant_id=self.tenant.id,
            payload=AddMemberRequest(user_id=member.id, role=MembershipRoles.MEMBER.value),
            invited_by_id=self.owner.id,
        )

        assert membership.tenant_id == self.tenant.id
        assert membership.user_id == member.id
        assert membership.role == MembershipRoles.MEMBER.value
        assert membership.invited_by_id == self.owner.id
        assert membership.left_at is None

    def test_add_member_raises_if_tenant_not_found(self):
        member = make_user("member@example.com")

        with pytest.raises(TenantNotFoundError, match="Tenant 999 not found"):
            TenantService.add_member(
                tenant_id=999,
                payload=AddMemberRequest(user_id=member.id, role=MembershipRoles.MEMBER.value),
                invited_by_id=self.owner.id,
            )

    def test_add_member_raises_if_already_member(self):
        member = make_user("member@example.com")
        TenantService.add_member(
            tenant_id=self.tenant.id,
            payload=AddMemberRequest(user_id=member.id, role=MembershipRoles.MEMBER.value),
            invited_by_id=self.owner.id,
        )

        with pytest.raises(MemberAlreadyExistsError):
            TenantService.add_member(
                tenant_id=self.tenant.id,
                payload=AddMemberRequest(user_id=member.id, role=MembershipRoles.ADMIN.value),
                invited_by_id=self.owner.id,
            )

    def test_add_member_raises_on_invalid_role(self):
        member = make_user("member@example.com")
        payload = AddMemberRequest.model_construct(user_id=member.id, role="invalid-role")

        with pytest.raises(InvalidMemberRoleError, match="Invalid role"):
            TenantService.add_member(
                tenant_id=self.tenant.id,
                payload=payload,
                invited_by_id=self.owner.id,
            )

    def test_list_members_returns_memberships(self):
        member = make_user("member@example.com")
        TenantService.add_membership(
            tenant_id=self.tenant.id,
            user_id=self.owner.id,
            entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
            invited_by_id=None,
        )
        TenantService.add_member(
            tenant_id=self.tenant.id,
            payload=AddMemberRequest(user_id=member.id, role=MembershipRoles.MEMBER.value),
            invited_by_id=self.owner.id,
        )

        memberships = TenantService.list_members(self.tenant.id)

        assert len(memberships) == 2
        assert [m.user_id for m in memberships] == [self.owner.id, member.id]

    def test_list_members_raises_if_tenant_not_found(self):
        with pytest.raises(TenantNotFoundError, match="Tenant 999 not found"):
            TenantService.list_members(999)

    def test_remove_member_marks_membership_inactive(self):
        member = make_user("member@example.com")
        membership = TenantService.add_member(
            tenant_id=self.tenant.id,
            payload=AddMemberRequest(user_id=member.id, role=MembershipRoles.MEMBER.value),
            invited_by_id=self.owner.id,
        )

        removed = TenantService.remove_member(
            tenant_id=self.tenant.id,
            membership_id=membership.id,
            reason="Left the company",
        )

        assert removed.id == membership.id
        assert removed.left_at is not None
        assert removed.left_reason == "Left the company"
        stored = TenantMembershipModel.objects.get(id=membership.id)
        assert stored.left_at is not None

    def test_remove_member_raises_if_tenant_not_found(self):
        with pytest.raises(TenantNotFoundError, match="Tenant 999 not found"):
            TenantService.remove_member(tenant_id=999, membership_id=1, reason="")

    def test_remove_member_raises_if_membership_not_found(self):
        with pytest.raises(MemberNotFoundError, match="Membership not found or already inactive"):
            TenantService.remove_member(
                tenant_id=self.tenant.id, membership_id=999, reason=""
            )
