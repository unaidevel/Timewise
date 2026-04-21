from unittest.mock import patch

import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.tenants.dtos.dtos import TenantIn
from infra.tenants.exceptions import (
    InvalidTenantNameError,
    InvalidTenantSlugError,
    TenantAlreadyExistsError,
)
from infra.tenants.models import TenantMembershipModel, TenantModel
from infra.tenants.orchestrators.tenant_orchestrator import TenantOrchestrator
from product.workforce.models import RoleModel

EXPECTED_DEFAULT_ROLE_NAMES = ["Manager", "Employee", "Intern", "Freelance"]


def make_user(email: str = "owner@example.com"):
    return AuthRepository.create_user(
        email=email,
        full_name="Test User",
        password_hash=AuthService._hash_password("SecurePass123!"),
    )


class TenantOrchestratorCreateTests(TestCase):
    def test_create_returns_tenant_with_correct_data(self):
        owner = make_user()

        tenant = TenantOrchestrator.create(
            TenantIn(name="  Acme Corp  ", slug="  Acme-Corp  "),
            created_by_id=owner.id,
        )

        assert tenant.name == "Acme Corp"
        assert tenant.slug == "acme-corp"
        assert tenant.created_by_id == owner.id

    def test_create_adds_owner_membership(self):
        owner = make_user()

        tenant = TenantOrchestrator.create(
            TenantIn(name="Acme Corp", slug="acme"), created_by_id=owner.id
        )

        memberships = TenantMembershipModel.objects.filter(tenant_id=tenant.id)
        assert memberships.count() == 1
        membership = memberships.get()
        assert membership.user_id == owner.id
        assert membership.role == MembershipRoles.OWNER.value
        assert membership.invited_by_id is None
        assert membership.left_at is None

    def test_create_seeds_default_workforce_roles(self):
        owner = make_user()

        tenant = TenantOrchestrator.create(
            TenantIn(name="Acme Corp", slug="acme"), created_by_id=owner.id
        )

        roles = RoleModel.objects.filter(tenant_id=tenant.id).order_by("name")
        assert roles.count() == len(EXPECTED_DEFAULT_ROLE_NAMES)
        assert set(roles.values_list("name", flat=True)) == set(
            EXPECTED_DEFAULT_ROLE_NAMES
        )
        assert all(r.is_active for r in roles)

    def test_create_raises_if_slug_already_exists(self):
        owner = make_user()
        TenantOrchestrator.create(
            TenantIn(name="Acme Corp", slug="acme"), created_by_id=owner.id
        )

        with pytest.raises(TenantAlreadyExistsError, match="slug 'acme'"):
            TenantOrchestrator.create(
                TenantIn(name="Another Acme", slug="acme"), created_by_id=owner.id
            )

    def test_create_raises_on_blank_name(self):
        owner = make_user()

        with pytest.raises(InvalidTenantNameError):
            TenantOrchestrator.create(
                TenantIn(name="   ", slug="acme"), created_by_id=owner.id
            )

    def test_create_raises_on_invalid_slug(self):
        owner = make_user()

        with pytest.raises(InvalidTenantSlugError):
            TenantOrchestrator.create(
                TenantIn(name="Acme Corp", slug="-invalid"), created_by_id=owner.id
            )

    def test_create_rolls_back_if_default_roles_fail(self):
        owner = make_user()

        with patch(
            "infra.tenants.orchestrators.tenant_orchestrator.WorkforceService"
        ) as mock_workforce:
            mock_workforce.create_default_roles.side_effect = Exception("DB error")

            with pytest.raises(Exception, match="DB error"):
                TenantOrchestrator.create(
                    TenantIn(name="Acme Corp", slug="acme"), created_by_id=owner.id
                )

        assert not TenantModel.objects.filter(slug="acme").exists()
        assert TenantMembershipModel.objects.count() == 0
