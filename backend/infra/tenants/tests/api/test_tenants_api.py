import pytest
from django.test import TestCase
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from infra.authz.api import router as auth_router
from infra.authz.api.dependencies import get_current_user
from infra.authz.dtos.dtos import LoginRequest, RegisterRequest
from infra.common.classes import MembershipRoles
from infra.tenants.api import router as tenants_router
from infra.tenants.dtos.dtos import (
    AddMemberRequest,
    OrganizationProfileIn,
    TenantIn,
)


def build_request(
    path: str = "/api/v1/auth/login", client_host: str = "127.0.0.1"
) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": path,
            "headers": [],
            "client": (client_host, 1234),
        }
    )


class TenantsApiTests(TestCase):
    def _authenticate_user(self, *, email: str, full_name: str):
        auth_router.register(
            RegisterRequest(
                email=email,
                full_name=full_name,
                password="SecurePass123!",
            ),
            build_request("/api/v1/auth/register"),
        )
        login_response = auth_router.login_user(
            LoginRequest(email=email, password="SecurePass123!"),
            build_request("/api/v1/auth/login"),
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=login_response.access_token,
        )
        return get_current_user(credentials)

    def test_create_tenant_returns_created_tenant(self):
        current_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )

        tenant = tenants_router.create(
            TenantIn(name="  Acme Corp  ", slug="  Acme-Corp  "),
            current_user=current_user,
            request=build_request(),
        )

        assert tenant.name == "Acme Corp"
        assert tenant.slug == "acme-corp"
        assert tenant.created_by_id == current_user.id

    def test_create_tenant_returns_409_when_slug_exists(self):
        current_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        tenants_router.create(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=current_user,
            request=build_request(),
        )

        with pytest.raises(HTTPException) as exc:
            tenants_router.create(
                TenantIn(name="Another Acme", slug="  ACME  "),
                current_user=current_user,
                request=build_request(),
            )

        assert exc.value.status_code == 409
        assert exc.value.detail == "A tenant with slug 'acme' already exists."

    def test_create_tenant_returns_422_for_invalid_domain_values(self):
        current_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )

        with pytest.raises(HTTPException) as exc:
            tenants_router.create(
                TenantIn(name="   ", slug="acme"),
                current_user=current_user,
                request=build_request(),
            )

        assert exc.value.status_code == 422
        assert exc.value.detail == "Tenant name cannot be blank."

    def test_list_for_user_returns_only_caller_tenants(self):
        owner_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        other_user = self._authenticate_user(
            email="other@example.com",
            full_name="Other User",
        )
        tenants_router.create(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=owner_user,
            request=build_request(),
        )
        tenants_router.create(
            TenantIn(name="Beta Corp", slug="beta"),
            current_user=other_user,
            request=build_request(),
        )

        tenants = tenants_router.list_for_user(owner_user, request=build_request())

        assert [t.slug for t in tenants] == ["acme"]

    def test_list_for_user_returns_empty_when_user_has_no_tenants(self):
        current_user = self._authenticate_user(
            email="loner@example.com",
            full_name="Loner User",
        )

        assert tenants_router.list_for_user(current_user, request=build_request()) == []

    def test_get_tenant_returns_tenant(self):
        current_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        created = tenants_router.create(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=current_user,
            request=build_request(),
        )

        tenant = tenants_router.get_by_id(
            created.id, current_user, request=build_request()
        )

        assert tenant.id == created.id
        assert tenant.slug == "acme"

    def test_add_member_returns_created_membership(self):
        owner_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        member_user = self._authenticate_user(
            email="member@example.com",
            full_name="Member User",
        )
        tenant = tenants_router.create(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=owner_user,
            request=build_request(),
        )

        membership = tenants_router.add_member(
            tenant_id=tenant.id,
            payload=AddMemberRequest(
                user_id=member_user.id,
                role=MembershipRoles.EMPLOYEE.value,
            ),
            current_user=owner_user,
            request=build_request(),
        )

        assert membership.tenant_id == tenant.id
        assert membership.user_id == member_user.id
        assert membership.role == MembershipRoles.EMPLOYEE.value
        assert membership.invited_by_id == owner_user.id

    def test_add_member_returns_404_when_tenant_is_missing(self):
        owner_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        member_user = self._authenticate_user(
            email="member@example.com",
            full_name="Member User",
        )

        with pytest.raises(HTTPException) as exc:
            tenants_router.add_member(
                tenant_id=999,
                payload=AddMemberRequest(
                    user_id=member_user.id,
                    role=MembershipRoles.EMPLOYEE.value,
                ),
                current_user=owner_user,
                request=build_request(),
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Tenant 999 not found."

    def test_add_member_returns_409_for_duplicate_active_membership(self):
        owner_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        member_user = self._authenticate_user(
            email="member@example.com",
            full_name="Member User",
        )
        tenant = tenants_router.create(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=owner_user,
            request=build_request(),
        )
        tenants_router.add_member(
            tenant_id=tenant.id,
            payload=AddMemberRequest(
                user_id=member_user.id,
                role=MembershipRoles.EMPLOYEE.value,
            ),
            current_user=owner_user,
            request=build_request(),
        )

        with pytest.raises(HTTPException) as exc:
            tenants_router.add_member(
                tenant_id=tenant.id,
                payload=AddMemberRequest(
                    user_id=member_user.id,
                    role=MembershipRoles.ADMIN.value,
                ),
                current_user=owner_user,
                request=build_request(),
            )

        assert exc.value.status_code == 409
        assert exc.value.detail == "User is already an active member."

    def test_add_member_returns_422_for_invalid_role(self):
        owner_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        member_user = self._authenticate_user(
            email="member@example.com",
            full_name="Member User",
        )
        tenant = tenants_router.create(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=owner_user,
            request=build_request(),
        )
        payload = AddMemberRequest.model_construct(
            user_id=member_user.id,
            role="invalid-role",
        )

        with pytest.raises(HTTPException) as exc:
            tenants_router.add_member(
                tenant_id=tenant.id,
                payload=payload,
                current_user=owner_user,
                request=build_request(),
            )

        assert exc.value.status_code == 422
        assert "Invalid role" in exc.value.detail

    def test_list_members_returns_tenant_memberships(self):
        owner_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        member_user = self._authenticate_user(
            email="member@example.com",
            full_name="Member User",
        )
        tenant = tenants_router.create(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=owner_user,
            request=build_request(),
        )
        tenants_router.add_member(
            tenant_id=tenant.id,
            payload=AddMemberRequest(
                user_id=member_user.id,
                role=MembershipRoles.EMPLOYEE.value,
            ),
            current_user=owner_user,
            request=build_request(),
        )

        memberships = tenants_router.list_members(
            tenant.id, owner_user, request=build_request()
        )

        assert len(memberships) == 2
        assert [membership.user_id for membership in memberships] == [
            owner_user.id,
            member_user.id,
        ]

    def test_list_members_returns_404_when_tenant_is_missing(self):
        current_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )

        with pytest.raises(HTTPException) as exc:
            tenants_router.list_members(999, current_user, request=build_request())

        assert exc.value.status_code == 404
        assert exc.value.detail == "Tenant 999 not found."

    def test_remove_member_returns_removed_membership(self):
        owner_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        member_user = self._authenticate_user(
            email="member@example.com",
            full_name="Member User",
        )
        tenant = tenants_router.create(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=owner_user,
            request=build_request(),
        )
        membership = tenants_router.add_member(
            tenant_id=tenant.id,
            payload=AddMemberRequest(
                user_id=member_user.id,
                role=MembershipRoles.EMPLOYEE.value,
            ),
            current_user=owner_user,
            request=build_request(),
        )

        removed = tenants_router.remove_member(
            tenant_id=tenant.id,
            membership_id=membership.id,
            _=owner_user,
            request=build_request(),
        )

        assert removed.id == membership.id
        assert removed.left_at is not None
        assert removed.left_reason is None

    def test_remove_member_returns_404_when_tenant_is_missing(self):
        current_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )

        with pytest.raises(HTTPException) as exc:
            tenants_router.remove_member(
                tenant_id=999,
                membership_id=1,
                _=current_user,
                request=build_request(),
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Tenant 999 not found."

    def test_remove_member_returns_404_when_membership_is_missing(self):
        owner_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        tenant = tenants_router.create(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=owner_user,
            request=build_request(),
        )

        with pytest.raises(HTTPException) as exc:
            tenants_router.remove_member(
                tenant_id=tenant.id,
                membership_id=999,
                _=owner_user,
                request=build_request(),
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Membership not found or already inactive."


def _profile_payload(**overrides) -> OrganizationProfileIn:
    base = dict(
        public_name="Acme",
        legal_name="Acme S.L.",
        country="ES",
        timezone="Europe/Madrid",
        currency="EUR",
        vat_number="ESB12345678",
    )
    base.update(overrides)
    return OrganizationProfileIn(**base)


class OrganizationProfileApiTests(TenantsApiTests):
    """Reuses the auth helper from TenantsApiTests."""

    def _setup_tenant_with_owner(self):
        owner = self._authenticate_user(
            email="owner@example.com", full_name="Owner User"
        )
        tenant = tenants_router.create(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=owner,
            request=build_request(),
        )
        return owner, tenant

    def test_get_organization_profile_returns_auto_created_defaults(self):
        owner, tenant = self._setup_tenant_with_owner()

        profile = tenants_router.get_organization_profile(
            tenant.id, owner, request=build_request()
        )

        assert profile.tenant_id == tenant.id
        assert profile.currency == "EUR"
        assert profile.timezone == "UTC"

    def test_get_organization_profile_returns_403_for_non_member(self):
        _, tenant = self._setup_tenant_with_owner()
        outsider = self._authenticate_user(
            email="outsider@example.com", full_name="Out Sider"
        )

        with pytest.raises(HTTPException) as exc:
            tenants_router.get_organization_profile(
                tenant.id, outsider, request=build_request()
            )

        assert exc.value.status_code == 403

    def test_update_organization_profile_persists_changes_for_owner(self):
        owner, tenant = self._setup_tenant_with_owner()

        updated = tenants_router.update_organization_profile(
            tenant.id,
            _profile_payload(public_name="Updated"),
            owner,
            request=build_request(),
        )

        assert updated.public_name == "Updated"
        roundtrip = tenants_router.get_organization_profile(
            tenant.id, owner, request=build_request()
        )
        assert roundtrip.public_name == "Updated"

    def test_update_organization_profile_returns_403_for_employee(self):
        owner, tenant = self._setup_tenant_with_owner()
        employee = self._authenticate_user(email="emp@example.com", full_name="Emp")
        tenants_router.add_member(
            tenant_id=tenant.id,
            payload=AddMemberRequest(
                user_id=employee.id, role=MembershipRoles.EMPLOYEE.value
            ),
            current_user=owner,
            request=build_request(),
        )

        with pytest.raises(HTTPException) as exc:
            tenants_router.update_organization_profile(
                tenant.id,
                _profile_payload(public_name="No"),
                employee,
                request=build_request(),
            )

        assert exc.value.status_code == 403

    def test_update_organization_profile_returns_422_for_invalid_timezone(self):
        owner, tenant = self._setup_tenant_with_owner()

        with pytest.raises(HTTPException) as exc:
            tenants_router.update_organization_profile(
                tenant.id,
                _profile_payload(timezone="Mars/Olympus"),
                owner,
                request=build_request(),
            )

        assert exc.value.status_code == 422
        assert "timezone" in exc.value.detail

    def test_update_organization_profile_returns_422_for_invalid_currency(self):
        owner, tenant = self._setup_tenant_with_owner()

        with pytest.raises(HTTPException) as exc:
            tenants_router.update_organization_profile(
                tenant.id,
                _profile_payload(currency="EU"),
                owner,
                request=build_request(),
            )

        assert exc.value.status_code == 422
        assert "currency" in exc.value.detail


class TimezonesApiTests(TenantsApiTests):
    def test_list_timezones_returns_curated_options_for_authenticated_user(self):
        user = self._authenticate_user(email="u@example.com", full_name="U")

        options = tenants_router.list_timezones(user, request=build_request())

        assert len(options) > 0
        values = {opt.value for opt in options}
        assert "UTC" in values
        assert "Europe/Madrid" in values
        # Labels carry the UTC offset.
        for opt in options:
            assert opt.label.startswith("(UTC")
