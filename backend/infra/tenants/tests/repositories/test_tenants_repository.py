from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.models import TenantMembershipModel
from infra.tenants.repositories.tenants_repository import TenantRepository


def make_user(email: str = "owner@example.com"):
    return AuthRepository.create_user(
        email=email,
        full_name="Test User",
        password_hash=AuthService._hash_password("SecurePass123!"),
    )


class TenantRepositoryTests(TestCase):
    def test_create_persists_tenant_and_get_by_id_returns_it(self):
        user = make_user()

        created = TenantRepository.create(
            TenantEntity(name="Acme Corp", slug="acme-corp"),
            user_id=user.id,
        )
        found = TenantRepository.get_by_id(created.id)

        assert found == created
        assert found.name == "Acme Corp"
        assert found.slug == "acme-corp"
        assert found.created_by_id == user.id

    def test_create_raises_type_error_for_non_entity_payload(self):
        user = make_user()

        with pytest.raises(TypeError, match="Expected TenantEntity"):
            TenantRepository.create("not-an-entity", user_id=user.id)

    def test_get_by_id_returns_none_for_unknown_tenant(self):
        assert TenantRepository.get_by_id(999) is None

    def test_find_by_slug_returns_tenant(self):
        user = make_user()
        created = TenantRepository.create(
            TenantEntity(name="Acme Corp", slug="acme-corp"),
            user_id=user.id,
        )

        found = TenantRepository.find_by_slug("acme-corp")

        assert found == created

    def test_find_by_slug_returns_none_for_unknown_slug(self):
        assert TenantRepository.find_by_slug("unknown-slug") is None

    def test_create_raises_integrity_error_on_duplicate_slug(self):
        user = make_user()
        TenantRepository.create(
            TenantEntity(name="Acme Corp", slug="acme-corp"),
            user_id=user.id,
        )

        with pytest.raises(IntegrityError):
            TenantRepository.create(
                TenantEntity(name="Another Acme", slug="acme-corp"),
                user_id=user.id,
            )

    def test_add_membership_creates_and_find_active_membership_returns_it(self):
        owner = make_user()
        member = make_user("member@example.com")
        tenant = TenantRepository.create(
            TenantEntity(name="Acme Corp", slug="acme"),
            user_id=owner.id,
        )

        created = TenantRepository.add_membership(
            tenant_id=tenant.id,
            user_id=member.id,
            entity=TenantMembershipEntity(role=MembershipRoles.EMPLOYEE.value),
            invited_by_id=owner.id,
        )
        found = TenantRepository.find_active_membership(tenant.id, member.id)

        assert found == created
        assert found.invited_by_id == owner.id
        assert found.left_at is None

    def test_add_membership_raises_type_error_for_non_entity_payload(self):
        owner = make_user()
        member = make_user("member@example.com")
        tenant = TenantRepository.create(
            TenantEntity(name="Acme Corp", slug="acme"),
            user_id=owner.id,
        )

        with pytest.raises(TypeError, match="Expected TenantMembershipEntity"):
            TenantRepository.add_membership(
                tenant_id=tenant.id,
                user_id=member.id,
                entity="not-an-entity",
                invited_by_id=owner.id,
            )

    def test_add_membership_raises_integrity_error_for_duplicate_active_member(self):
        owner = make_user()
        member = make_user("member@example.com")
        tenant = TenantRepository.create(
            TenantEntity(name="Acme Corp", slug="acme"),
            user_id=owner.id,
        )
        TenantRepository.add_membership(
            tenant_id=tenant.id,
            user_id=member.id,
            entity=TenantMembershipEntity(role=MembershipRoles.EMPLOYEE.value),
            invited_by_id=owner.id,
        )

        with pytest.raises(IntegrityError):
            TenantRepository.add_membership(
                tenant_id=tenant.id,
                user_id=member.id,
                entity=TenantMembershipEntity(role=MembershipRoles.ADMIN.value),
                invited_by_id=owner.id,
            )

    def test_find_active_membership_returns_none_when_missing_or_inactive(self):
        owner = make_user()
        member = make_user("member@example.com")
        tenant = TenantRepository.create(
            TenantEntity(name="Acme Corp", slug="acme"),
            user_id=owner.id,
        )
        membership = TenantRepository.add_membership(
            tenant_id=tenant.id,
            user_id=member.id,
            entity=TenantMembershipEntity(role=MembershipRoles.EMPLOYEE.value),
            invited_by_id=owner.id,
        )
        TenantRepository.remove_membership(
            membership.id, "Removed", left_at=timezone.now()
        )

        assert TenantRepository.find_active_membership(tenant.id, member.id) is None
        assert TenantRepository.find_active_membership(tenant.id, 999) is None

    def test_list_memberships_returns_memberships_in_joined_at_order(self):
        owner = make_user()
        first_member = make_user("first@example.com")
        second_member = make_user("second@example.com")
        tenant = TenantRepository.create(
            TenantEntity(name="Acme Corp", slug="acme"),
            user_id=owner.id,
        )
        first = TenantRepository.add_membership(
            tenant_id=tenant.id,
            user_id=first_member.id,
            entity=TenantMembershipEntity(role=MembershipRoles.ADMIN.value),
            invited_by_id=owner.id,
        )
        second = TenantRepository.add_membership(
            tenant_id=tenant.id,
            user_id=second_member.id,
            entity=TenantMembershipEntity(role=MembershipRoles.EMPLOYEE.value),
            invited_by_id=owner.id,
        )

        now = timezone.now()
        TenantMembershipModel.objects.filter(id=first.id).update(
            joined_at=now + timedelta(minutes=5)
        )
        TenantMembershipModel.objects.filter(id=second.id).update(joined_at=now)

        memberships = TenantRepository.list_memberships(tenant.id)

        assert [membership.id for membership in memberships] == [second.id, first.id]

    def test_remove_membership_sets_left_at_and_reason(self):
        owner = make_user()
        member = make_user("member@example.com")
        tenant = TenantRepository.create(
            TenantEntity(name="Acme Corp", slug="acme"),
            user_id=owner.id,
        )
        membership = TenantRepository.add_membership(
            tenant_id=tenant.id,
            user_id=member.id,
            entity=TenantMembershipEntity(role=MembershipRoles.EMPLOYEE.value),
            invited_by_id=owner.id,
        )

        removed = TenantRepository.remove_membership(
            membership.id, "Resigned", left_at=timezone.now()
        )

        assert removed is not None
        assert removed.left_at is not None
        assert removed.left_reason == "Resigned"

    def test_list_for_user_returns_tenants_where_user_is_active_member(self):
        owner = make_user()
        other = make_user("other@example.com")
        first = TenantRepository.create(
            TenantEntity(name="Beta Corp", slug="beta"),
            user_id=owner.id,
        )
        second = TenantRepository.create(
            TenantEntity(name="Acme Corp", slug="acme"),
            user_id=owner.id,
        )
        third = TenantRepository.create(
            TenantEntity(name="Gamma Corp", slug="gamma"),
            user_id=other.id,
        )
        TenantRepository.add_membership(
            tenant_id=first.id,
            user_id=owner.id,
            entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
            invited_by_id=None,
        )
        TenantRepository.add_membership(
            tenant_id=second.id,
            user_id=owner.id,
            entity=TenantMembershipEntity(role=MembershipRoles.EMPLOYEE.value),
            invited_by_id=None,
        )
        TenantRepository.add_membership(
            tenant_id=third.id,
            user_id=other.id,
            entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
            invited_by_id=None,
        )

        tenants = TenantRepository.list_for_user(owner.id)

        assert [t.slug for t in tenants] == ["acme", "beta"]

    def test_list_for_user_excludes_left_memberships(self):
        owner = make_user()
        tenant = TenantRepository.create(
            TenantEntity(name="Acme Corp", slug="acme"),
            user_id=owner.id,
        )
        membership = TenantRepository.add_membership(
            tenant_id=tenant.id,
            user_id=owner.id,
            entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
            invited_by_id=None,
        )
        TenantRepository.remove_membership(
            membership.id, "left", left_at=timezone.now()
        )

        assert TenantRepository.list_for_user(owner.id) == []

    def test_list_for_user_returns_empty_for_user_without_memberships(self):
        loner = make_user("loner@example.com")
        assert TenantRepository.list_for_user(loner.id) == []

    def test_remove_membership_returns_none_for_missing_or_inactive_membership(self):
        owner = make_user()
        member = make_user("member@example.com")
        tenant = TenantRepository.create(
            TenantEntity(name="Acme Corp", slug="acme"),
            user_id=owner.id,
        )
        membership = TenantRepository.add_membership(
            tenant_id=tenant.id,
            user_id=member.id,
            entity=TenantMembershipEntity(role=MembershipRoles.EMPLOYEE.value),
            invited_by_id=owner.id,
        )
        TenantRepository.remove_membership(
            membership.id, "Resigned", left_at=timezone.now()
        )

        assert (
            TenantRepository.remove_membership(999, "", left_at=timezone.now()) is None
        )
        assert (
            TenantRepository.remove_membership(
                membership.id, "", left_at=timezone.now()
            )
            is None
        )
