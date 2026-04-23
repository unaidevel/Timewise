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
from infra.tenants.dtos.dtos import AddMemberRequest, TenantIn


def build_request(path: str, client_host: str = "127.0.0.1") -> Request:
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
            )
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

        tenant = tenants_router.create_tenant(
            TenantIn(name="  Acme Corp  ", slug="  Acme-Corp  "),
            current_user=current_user,
        )

        assert tenant.name == "Acme Corp"
        assert tenant.slug == "acme-corp"
        assert tenant.created_by_id == current_user.id

    def test_create_tenant_returns_409_when_slug_exists(self):
        current_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        tenants_router.create_tenant(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=current_user,
        )

        with pytest.raises(HTTPException) as exc:
            tenants_router.create_tenant(
                TenantIn(name="Another Acme", slug="  ACME  "),
                current_user=current_user,
            )

        assert exc.value.status_code == 409
        assert exc.value.detail == "A tenant with slug 'acme' already exists."

    def test_create_tenant_returns_422_for_invalid_domain_values(self):
        current_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )

        with pytest.raises(HTTPException) as exc:
            tenants_router.create_tenant(
                TenantIn(name="   ", slug="acme"),
                current_user=current_user,
            )

        assert exc.value.status_code == 422
        assert exc.value.detail == "Tenant name cannot be blank."

    def test_list_tenants_returns_all_tenants(self):
        current_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        tenants_router.create_tenant(
            TenantIn(name="Zulu", slug="zulu"),
            current_user=current_user,
        )
        tenants_router.create_tenant(
            TenantIn(name="Alpha", slug="alpha"),
            current_user=current_user,
        )

        tenants = tenants_router.list_tenants(current_user)

        assert [tenant.name for tenant in tenants] == ["Alpha", "Zulu"]

    def test_get_tenant_returns_tenant(self):
        current_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        created = tenants_router.create_tenant(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=current_user,
        )

        tenant = tenants_router.get_tenant(created.id, current_user)

        assert tenant.id == created.id
        assert tenant.slug == "acme"

    def test_get_tenant_returns_404_when_missing(self):
        current_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )

        with pytest.raises(HTTPException) as exc:
            tenants_router.get_tenant(999, current_user)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Tenant 999 not found."

    def test_add_member_returns_created_membership(self):
        owner_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        member_user = self._authenticate_user(
            email="member@example.com",
            full_name="Member User",
        )
        tenant = tenants_router.create_tenant(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=owner_user,
        )

        membership = tenants_router.add_member(
            tenant_id=tenant.id,
            payload=AddMemberRequest(
                user_id=member_user.id,
                role=MembershipRoles.EMPLOYEE.value,
            ),
            current_user=owner_user,
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
        tenant = tenants_router.create_tenant(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=owner_user,
        )
        tenants_router.add_member(
            tenant_id=tenant.id,
            payload=AddMemberRequest(
                user_id=member_user.id,
                role=MembershipRoles.EMPLOYEE.value,
            ),
            current_user=owner_user,
        )

        with pytest.raises(HTTPException) as exc:
            tenants_router.add_member(
                tenant_id=tenant.id,
                payload=AddMemberRequest(
                    user_id=member_user.id,
                    role=MembershipRoles.ADMIN.value,
                ),
                current_user=owner_user,
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
        tenant = tenants_router.create_tenant(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=owner_user,
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
        tenant = tenants_router.create_tenant(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=owner_user,
        )
        tenants_router.add_member(
            tenant_id=tenant.id,
            payload=AddMemberRequest(
                user_id=member_user.id,
                role=MembershipRoles.EMPLOYEE.value,
            ),
            current_user=owner_user,
        )

        memberships = tenants_router.list_members(tenant.id, owner_user)

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
            tenants_router.list_members(999, current_user)

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
        tenant = tenants_router.create_tenant(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=owner_user,
        )
        membership = tenants_router.add_member(
            tenant_id=tenant.id,
            payload=AddMemberRequest(
                user_id=member_user.id,
                role=MembershipRoles.EMPLOYEE.value,
            ),
            current_user=owner_user,
        )

        removed = tenants_router.remove_member(
            tenant_id=tenant.id,
            membership_id=membership.id,
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
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Tenant 999 not found."

    def test_remove_member_returns_404_when_membership_is_missing(self):
        owner_user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner User",
        )
        tenant = tenants_router.create_tenant(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=owner_user,
        )

        with pytest.raises(HTTPException) as exc:
            tenants_router.remove_member(
                tenant_id=tenant.id,
                membership_id=999,
                _=owner_user,
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Membership not found or already inactive."
