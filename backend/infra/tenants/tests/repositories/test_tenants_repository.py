from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.tenants.exceptions import MemberAlreadyExistsError, TenantAlreadyExistsError
from infra.tenants.models import TENANT_ROLE_MEMBER, TENANT_ROLE_OWNER
from infra.tenants.repositories.tenants_repository import TenantRepository


def make_user(email: str = "owner@example.com") -> object:
    return AuthRepository.create_user(
        email=email,
        full_name="Test User",
        password_hash=AuthService._hash_password("SecurePass123!"),
    )


class TenantRepositoryTests(TestCase):
    def test_create_and_find_tenant(self):
        user = make_user()
        tenant = TenantRepository.create("Acme Corp", "acme-corp", user.id)

        found = TenantRepository.get_by_id(tenant.id)

        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Acme Corp")
        self.assertEqual(found.slug, "acme-corp")
        self.assertTrue(found.is_active)

    def test_find_by_slug(self):
        user = make_user()
        TenantRepository.create("Acme Corp", "acme-corp", user.id)

        found = TenantRepository.find_by_slug("acme-corp")

        self.assertIsNotNone(found)
        self.assertEqual(found.slug, "acme-corp")

    def test_find_by_slug_returns_none_for_unknown(self):
        result = TenantRepository.find_by_slug("unknown-slug")
        self.assertIsNone(result)

    def test_create_raises_on_duplicate_slug(self):
        user = make_user()
        TenantRepository.create("Acme Corp", "acme-corp", user.id)

        with self.assertRaises(TenantAlreadyExistsError):
            TenantRepository.create("Acme Corp 2", "acme-corp", user.id)

    def test_list_all_returns_all_tenants(self):
        user = make_user()
        TenantRepository.create("Alpha", "alpha", user.id)
        TenantRepository.create("Beta", "beta", user.id)

        tenants = TenantRepository.list_all()

        self.assertEqual(len(tenants), 2)

    def test_add_and_find_active_membership(self):
        user = make_user()
        tenant = TenantRepository.create("Acme", "acme", user.id)

        membership = TenantRepository.add_membership(
            tenant_id=tenant.id,
            user_id=user.id,
            role=TENANT_ROLE_OWNER,
            invited_by_id=None,
        )

        found = TenantRepository.find_active_membership(tenant.id, user.id)

        self.assertIsNotNone(found)
        self.assertEqual(found.role, TENANT_ROLE_OWNER)
        self.assertEqual(membership.user_id, user.id)

    def test_add_membership_raises_on_duplicate_active(self):
        user = make_user()
        tenant = TenantRepository.create("Acme", "acme", user.id)
        TenantRepository.add_membership(tenant.id, user.id, TENANT_ROLE_OWNER, None)

        with self.assertRaises(MemberAlreadyExistsError):
            TenantRepository.add_membership(tenant.id, user.id, TENANT_ROLE_MEMBER, None)

    def test_remove_membership_sets_left_at(self):
        user = make_user()
        member = make_user("member@example.com")
        tenant = TenantRepository.create("Acme", "acme", user.id)
        membership = TenantRepository.add_membership(
            tenant.id, member.id, TENANT_ROLE_MEMBER, user.id
        )

        removed = TenantRepository.remove_membership(membership.id, "Resigned")

        self.assertIsNotNone(removed.left_at)
        self.assertEqual(removed.left_reason, "Resigned")
        self.assertIsNone(TenantRepository.find_active_membership(tenant.id, member.id))

    def test_list_memberships(self):
        user = make_user()
        member = make_user("member@example.com")
        tenant = TenantRepository.create("Acme", "acme", user.id)
        TenantRepository.add_membership(tenant.id, user.id, TENANT_ROLE_OWNER, None)
        TenantRepository.add_membership(tenant.id, member.id, TENANT_ROLE_MEMBER, user.id)

        memberships = TenantRepository.list_memberships(tenant.id)

        self.assertEqual(len(memberships), 2)
