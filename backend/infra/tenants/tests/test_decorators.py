import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.common.exceptions import Forbidden
from infra.tenants.decorators import (
    any_employee,
    only_admin,
    only_manager,
    only_owner,
    require_membership_role,
)
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.services.tenants_service import TenantService


def make_user(email: str):
    return AuthRepository.create_user(
        email=email,
        full_name="Test User",
        password_hash=AuthService._hash_password("SecurePass123!"),
    )


def make_tenant(user_id: int, slug: str = "acme"):
    return TenantService.create(
        TenantEntity(name="Acme Corp", slug=slug), user_id=user_id
    )


def add_member(tenant_id: int, user_id: int, role: MembershipRoles):
    TenantService.add_membership(
        tenant_id=tenant_id,
        user_id=user_id,
        entity=TenantMembershipEntity(role=role.value),
        invited_by_id=None,
    )


class RequireMembershipRoleDecoratorTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner@example.com")
        self.tenant = make_tenant(self.owner.id)
        self.admin = make_user("admin@example.com")
        self.manager = make_user("manager@example.com")
        self.employee = make_user("employee@example.com")
        self.outsider = make_user("outsider@example.com")
        add_member(self.tenant.id, self.owner.id, MembershipRoles.OWNER)
        add_member(self.tenant.id, self.admin.id, MembershipRoles.ADMIN)
        add_member(self.tenant.id, self.manager.id, MembershipRoles.MANAGER)
        add_member(self.tenant.id, self.employee.id, MembershipRoles.EMPLOYEE)

    def test_only_owner_allows_owner(self):
        @only_owner
        @staticmethod
        def op(tenant_id: int, user_id: int) -> str:
            return "ok"

        assert op(tenant_id=self.tenant.id, user_id=self.owner.id) == "ok"

    def test_only_owner_rejects_admin(self):
        @only_owner
        @staticmethod
        def op(tenant_id: int, user_id: int) -> str:
            return "ok"

        with pytest.raises(Forbidden):
            op(tenant_id=self.tenant.id, user_id=self.admin.id)

    def test_only_admin_accepts_owner_and_admin(self):
        @only_admin
        @staticmethod
        def op(tenant_id: int, user_id: int) -> str:
            return "ok"

        assert op(tenant_id=self.tenant.id, user_id=self.owner.id) == "ok"
        assert op(tenant_id=self.tenant.id, user_id=self.admin.id) == "ok"

    def test_only_admin_rejects_manager(self):
        @only_admin
        @staticmethod
        def op(tenant_id: int, user_id: int) -> str:
            return "ok"

        with pytest.raises(Forbidden):
            op(tenant_id=self.tenant.id, user_id=self.manager.id)

    def test_only_manager_rejects_employee(self):
        @only_manager
        @staticmethod
        def op(tenant_id: int, user_id: int) -> str:
            return "ok"

        with pytest.raises(Forbidden):
            op(tenant_id=self.tenant.id, user_id=self.employee.id)

    def test_only_manager_accepts_manager_admin_owner(self):
        @only_manager
        @staticmethod
        def op(tenant_id: int, user_id: int) -> str:
            return "ok"

        assert op(tenant_id=self.tenant.id, user_id=self.manager.id) == "ok"
        assert op(tenant_id=self.tenant.id, user_id=self.admin.id) == "ok"
        assert op(tenant_id=self.tenant.id, user_id=self.owner.id) == "ok"

    def test_any_employee_accepts_all_roles(self):
        @any_employee
        @staticmethod
        def op(tenant_id: int, user_id: int) -> str:
            return "ok"

        for user in (self.owner, self.admin, self.manager, self.employee):
            assert op(tenant_id=self.tenant.id, user_id=user.id) == "ok"

    def test_any_employee_rejects_outsider(self):
        @any_employee
        @staticmethod
        def op(tenant_id: int, user_id: int) -> str:
            return "ok"

        with pytest.raises(Forbidden):
            op(tenant_id=self.tenant.id, user_id=self.outsider.id)

    def test_decorator_skips_check_when_tenant_id_missing(self):
        @only_owner
        @staticmethod
        def op(user_id: int) -> str:
            return "ok"

        # No tenant_id parameter -> decorator can't check, must allow.
        assert op(user_id=self.outsider.id) == "ok"

    def test_decorator_skips_check_when_user_id_is_none(self):
        @only_owner
        @staticmethod
        def op(tenant_id: int, user_id: int | None = None) -> str:
            return "ok"

        # user_id resolves to None -> decorator skips role check.
        assert op(tenant_id=self.tenant.id) == "ok"

    def test_decorator_rejects_when_membership_is_inactive(self):
        # Mark employee as left.
        from django.utils import timezone

        from infra.tenants.models import TenantMembershipModel

        TenantMembershipModel.objects.filter(
            tenant_id=self.tenant.id, user_id=self.employee.id
        ).update(left_at=timezone.now())

        @any_employee
        @staticmethod
        def op(tenant_id: int, user_id: int) -> str:
            return "ok"

        with pytest.raises(Forbidden):
            op(tenant_id=self.tenant.id, user_id=self.employee.id)

    def test_decorator_works_with_inverse_decorator_order(self):
        # @staticmethod outer, @require_membership_role inner.
        @staticmethod
        @require_membership_role(MembershipRoles.OWNER)
        def op(tenant_id: int, user_id: int) -> str:
            return "ok"

        assert op(tenant_id=self.tenant.id, user_id=self.owner.id) == "ok"
        with pytest.raises(Forbidden):
            op(tenant_id=self.tenant.id, user_id=self.admin.id)
