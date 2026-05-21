import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.common.exceptions import (
    Conflict,
    Forbidden,
    NotFound,
    UnprocessableEntity,
)
from infra.tenants.dtos.dtos import (
    AddMemberRequest,
    OrganizationProfileIn,
    TenantMemberResponse,
    TenantOut,
)
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.models import TenantMembershipModel
from infra.tenants.services.tenants_service import (
    OrganizationProfileService,
    TenantService,
)


def make_user(email: str = "owner@example.com"):
    return AuthRepository.create_user(
        email=email,
        full_name="Test User",
        password_hash=AuthService._hash_password("SecurePass123!"),
    )


def make_tenant(user_id: int, slug: str = "acme") -> TenantOut:
    return TenantService.create(
        TenantEntity(name="Acme Corp", slug=slug), user_id=user_id
    )


class TenantServiceCreateTests(TestCase):
    def test_create_returns_persisted_tenant(self):
        owner = make_user()

        tenant = TenantService.create(
            TenantEntity(name="Acme Corp", slug="acme"), user_id=owner.id
        )

        assert tenant.name == "Acme Corp"
        assert tenant.slug == "acme"
        assert tenant.created_by_id == owner.id
        assert isinstance(tenant, TenantOut)

    def test_create_does_not_create_membership(self):
        owner = make_user()

        TenantService.create(
            TenantEntity(name="Acme Corp", slug="acme"), user_id=owner.id
        )

        assert TenantMembershipModel.objects.count() == 0

    def test_create_raises_if_slug_already_exists(self):
        owner = make_user()
        TenantService.create(
            TenantEntity(name="Acme Corp", slug="acme"), user_id=owner.id
        )

        with pytest.raises(Conflict, match="slug 'acme'"):
            TenantService.create(
                TenantEntity(name="Another Acme", slug="acme"), user_id=owner.id
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
        TenantService.add_membership(
            tenant_id=created.id,
            user_id=owner.id,
            entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
            invited_by_id=None,
        )

        found = TenantService.get_by_id(created.id, user_id=owner.id)

        assert found == created


class TenantServiceListForUserTests(TestCase):
    def test_list_for_user_returns_tenants_user_is_member_of(self):
        owner = make_user()
        other = make_user("other@example.com")
        mine = make_tenant(owner.id, slug="acme")
        theirs = make_tenant(other.id, slug="beta")
        TenantService.add_membership(
            tenant_id=mine.id,
            user_id=owner.id,
            entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
            invited_by_id=None,
        )
        TenantService.add_membership(
            tenant_id=theirs.id,
            user_id=other.id,
            entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
            invited_by_id=None,
        )

        tenants = TenantService.list_for_user(owner.id)

        assert [t.slug for t in tenants] == ["acme"]

    def test_list_for_user_returns_empty_when_user_has_no_memberships(self):
        loner = make_user("loner@example.com")
        assert TenantService.list_for_user(loner.id) == []


class TenantServiceMemberTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.tenant = make_tenant(self.owner.id)

    def test_add_member_creates_membership(self):
        member = make_user("member@example.com")

        membership = TenantService.add_member(
            tenant_id=self.tenant.id,
            payload=AddMemberRequest(
                user_id=member.id, role=MembershipRoles.EMPLOYEE.value
            ),
            invited_by_id=self.owner.id,
        )

        assert membership.tenant_id == self.tenant.id
        assert membership.user_id == member.id
        assert membership.role == MembershipRoles.EMPLOYEE.value
        assert membership.invited_by_id == self.owner.id
        assert membership.left_at is None

    def test_add_member_raises_if_tenant_not_found(self):
        member = make_user("member@example.com")

        with pytest.raises(NotFound, match="Tenant 999 not found"):
            TenantService.add_member(
                tenant_id=999,
                payload=AddMemberRequest(
                    user_id=member.id, role=MembershipRoles.EMPLOYEE.value
                ),
                invited_by_id=self.owner.id,
            )

    def test_add_member_raises_if_already_member(self):
        member = make_user("member@example.com")
        TenantService.add_member(
            tenant_id=self.tenant.id,
            payload=AddMemberRequest(
                user_id=member.id, role=MembershipRoles.EMPLOYEE.value
            ),
            invited_by_id=self.owner.id,
        )

        with pytest.raises(Conflict):
            TenantService.add_member(
                tenant_id=self.tenant.id,
                payload=AddMemberRequest(
                    user_id=member.id, role=MembershipRoles.ADMIN.value
                ),
                invited_by_id=self.owner.id,
            )

    def test_add_member_raises_on_invalid_role(self):
        member = make_user("member@example.com")
        payload = AddMemberRequest.model_construct(
            user_id=member.id, role="invalid-role"
        )

        with pytest.raises(UnprocessableEntity, match="Invalid role"):
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
            payload=AddMemberRequest(
                user_id=member.id, role=MembershipRoles.EMPLOYEE.value
            ),
            invited_by_id=self.owner.id,
        )

        memberships = TenantService.list_members(self.tenant.id)

        assert len(memberships) == 2
        assert [m.user_id for m in memberships] == [self.owner.id, member.id]

    def test_list_members_raises_if_tenant_not_found(self):
        with pytest.raises(NotFound, match="Tenant 999 not found"):
            TenantService.list_members(999)

    def test_remove_member_marks_membership_inactive(self):
        member = make_user("member@example.com")
        membership = TenantService.add_member(
            tenant_id=self.tenant.id,
            payload=AddMemberRequest(
                user_id=member.id, role=MembershipRoles.EMPLOYEE.value
            ),
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
        with pytest.raises(NotFound, match="Tenant 999 not found"):
            TenantService.remove_member(tenant_id=999, membership_id=1, reason="")

    def test_remove_member_raises_if_membership_not_found(self):
        with pytest.raises(NotFound, match="Membership not found or already inactive"):
            TenantService.remove_member(
                tenant_id=self.tenant.id, membership_id=999, reason=""
            )


def _default_payload(**overrides) -> OrganizationProfileIn:
    base = dict(
        public_name="Acme",
        legal_name="Acme S.L.",
        workspace_name="acme",
        country="ES",
        timezone="Europe/Madrid",
        currency="EUR",
        fiscal_year_start="01-01",
        vat_number="ESB12345678",
        default_locale="es-ES",
    )
    base.update(overrides)
    return OrganizationProfileIn(**base)


class OrganizationProfileServiceTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.tenant = make_tenant(self.owner.id)
        TenantService.add_membership(
            tenant_id=self.tenant.id,
            user_id=self.owner.id,
            entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
            invited_by_id=None,
        )
        OrganizationProfileService.create_default(self.tenant.id)

    def test_create_default_returns_profile_with_backend_defaults(self):
        other_tenant = make_tenant(self.owner.id, slug="beta")

        profile = OrganizationProfileService.create_default(other_tenant.id)

        assert profile.tenant_id == other_tenant.id
        assert profile.currency == "EUR"
        assert profile.fiscal_year_start == "01-01"

    def test_get_returns_profile_for_any_member(self):
        employee = make_user("employee@example.com")
        TenantService.add_member(
            tenant_id=self.tenant.id,
            payload=AddMemberRequest(
                user_id=employee.id, role=MembershipRoles.EMPLOYEE.value
            ),
            invited_by_id=self.owner.id,
        )

        profile = OrganizationProfileService.get(self.tenant.id, employee.id)

        assert profile.tenant_id == self.tenant.id

    def test_get_raises_forbidden_for_non_member(self):
        outsider = make_user("outsider@example.com")

        with pytest.raises(Forbidden):
            OrganizationProfileService.get(self.tenant.id, outsider.id)

    def test_get_raises_not_found_when_profile_missing(self):
        other_tenant = make_tenant(self.owner.id, slug="beta")
        TenantService.add_membership(
            tenant_id=other_tenant.id,
            user_id=self.owner.id,
            entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
            invited_by_id=None,
        )

        with pytest.raises(NotFound, match="Organization profile"):
            OrganizationProfileService.get(other_tenant.id, self.owner.id)

    def test_update_persists_and_returns_changes_for_owner(self):
        updated = OrganizationProfileService.update(
            self.tenant.id, _default_payload(public_name="New"), self.owner.id
        )

        assert updated.public_name == "New"
        # Subsequent get returns the same data
        assert (
            OrganizationProfileService.get(self.tenant.id, self.owner.id).public_name
            == "New"
        )

    def test_update_allows_admins(self):
        admin = make_user("admin@example.com")
        TenantService.add_member(
            tenant_id=self.tenant.id,
            payload=AddMemberRequest(
                user_id=admin.id, role=MembershipRoles.ADMIN.value
            ),
            invited_by_id=self.owner.id,
        )

        updated = OrganizationProfileService.update(
            self.tenant.id, _default_payload(public_name="By Admin"), admin.id
        )

        assert updated.public_name == "By Admin"

    def test_update_rejects_non_admin_member(self):
        employee = make_user("employee@example.com")
        TenantService.add_member(
            tenant_id=self.tenant.id,
            payload=AddMemberRequest(
                user_id=employee.id, role=MembershipRoles.EMPLOYEE.value
            ),
            invited_by_id=self.owner.id,
        )

        with pytest.raises(Forbidden):
            OrganizationProfileService.update(
                self.tenant.id, _default_payload(), employee.id
            )

    def test_update_rejects_non_member(self):
        outsider = make_user("outsider@example.com")

        with pytest.raises(Forbidden):
            OrganizationProfileService.update(
                self.tenant.id, _default_payload(), outsider.id
            )

    def test_update_raises_unprocessable_for_invalid_timezone(self):
        with pytest.raises(UnprocessableEntity, match="timezone"):
            OrganizationProfileService.update(
                self.tenant.id,
                _default_payload(timezone="Mars/Olympus"),
                self.owner.id,
            )

    def test_update_raises_unprocessable_for_invalid_currency(self):
        with pytest.raises(UnprocessableEntity, match="currency"):
            OrganizationProfileService.update(
                self.tenant.id,
                _default_payload(currency="EU"),
                self.owner.id,
            )

    def test_update_raises_unprocessable_for_invalid_fiscal(self):
        with pytest.raises(UnprocessableEntity, match="fiscal_year_start"):
            OrganizationProfileService.update(
                self.tenant.id,
                _default_payload(fiscal_year_start="13-01"),
                self.owner.id,
            )

    def test_update_raises_not_found_when_profile_is_missing(self):
        other_tenant = make_tenant(self.owner.id, slug="beta")
        TenantService.add_membership(
            tenant_id=other_tenant.id,
            user_id=self.owner.id,
            entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
            invited_by_id=None,
        )

        with pytest.raises(NotFound, match="Organization profile"):
            OrganizationProfileService.update(
                other_tenant.id, _default_payload(), self.owner.id
            )
