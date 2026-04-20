import pytest
from django.utils import timezone

from infra.tenants.dtos.dtos import TenantIn
from infra.tenants.dtos.tenant_dtos import Tenant, TenantMembership
from infra.tenants.exceptions import (
    MemberAlreadyExistsError,
    InvalidTenantNameError,
    InvalidTenantSlugError,
    TenantAlreadyExistsError,
    TenantNotFoundError,
)
from infra.tenants.models import TENANT_ROLE_MEMBER, TENANT_ROLE_OWNER
from infra.tenants.services.tenants_service import TenantService


def make_tenant(slug: str = "acme") -> Tenant:
    now = timezone.now()
    return Tenant(
        id=1,
        name="Acme Corp",
        slug=slug,
        is_active=True,
        created_at=now,
        updated_at=now,
        created_by_id=10,
    )


def make_membership(
    tenant_id: int | None = None,
    user_id: int | None = None,
    role: str = TENANT_ROLE_OWNER,
) -> TenantMembership:
    return TenantMembership(
        id=1,
        tenant_id=tenant_id or 1,
        user_id=user_id or 20,
        role=role,
        joined_at=timezone.now(),
        invited_by_id=None,
        left_at=None,
        left_reason=None,
    )


def test_create_tenant_raises_if_slug_exists(monkeypatch):
    existing = make_tenant()
    monkeypatch.setattr(
        "infra.tenants.services.tenants_service.TenantRepository.find_by_slug",
        lambda slug: existing,
    )

    with pytest.raises(TenantAlreadyExistsError):
        TenantService.create(TenantIn(name="Acme Corp", slug="acme"), 10)


def test_create_tenant_raises_on_invalid_name():
    with pytest.raises(InvalidTenantNameError):
        TenantService.create(TenantIn(name="   ", slug="acme"), 10)


def test_create_tenant_raises_on_invalid_slug():
    with pytest.raises(InvalidTenantSlugError):
        TenantService.create(TenantIn(name="Acme Corp", slug="-invalid"), 10)


def test_create_tenant_normalizes_values_and_adds_owner_membership(monkeypatch):
    created_tenants = []
    added_memberships = []
    tenant = make_tenant()

    monkeypatch.setattr(
        "infra.tenants.services.tenants_service.TenantRepository.find_by_slug",
        lambda slug: None,
    )

    def fake_create(name, slug, created_by_id):
        created_tenants.append((name, slug, created_by_id))
        return tenant

    monkeypatch.setattr(
        "infra.tenants.services.tenants_service.TenantRepository.create",
        fake_create,
    )
    monkeypatch.setattr(
        "infra.tenants.services.tenants_service.TenantRepository.add_membership",
        lambda tenant_id, user_id, role, invited_by_id: added_memberships.append(role),
    )

    created_by_id = 10
    TenantService.create(
        TenantIn(name="  Acme Corp  ", slug="  Acme  "),
        created_by_id,
    )

    assert created_tenants == [("Acme Corp", "acme", created_by_id)]
    assert added_memberships == [TENANT_ROLE_OWNER]


def test_get_by_id_raises_if_not_found(monkeypatch):
    monkeypatch.setattr(
        "infra.tenants.services.tenants_service.TenantRepository.get_by_id",
        lambda tenant_id: None,
    )

    with pytest.raises(TenantNotFoundError):
        TenantService.get_by_id(999)


def test_add_member_raises_if_tenant_not_found(monkeypatch):
    monkeypatch.setattr(
        "infra.tenants.services.tenants_service.TenantRepository.get_by_id",
        lambda tenant_id: None,
    )

    with pytest.raises(TenantNotFoundError):
        TenantService.add_member(999, 20, TENANT_ROLE_MEMBER, 10)


def test_add_member_raises_if_already_member(monkeypatch):
    tenant = make_tenant()
    membership = make_membership(tenant_id=tenant.id)

    monkeypatch.setattr(
        "infra.tenants.services.tenants_service.TenantRepository.get_by_id",
        lambda tenant_id: tenant,
    )
    monkeypatch.setattr(
        "infra.tenants.services.tenants_service.TenantRepository.find_active_membership",
        lambda tenant_id, user_id: membership,
    )

    with pytest.raises(MemberAlreadyExistsError):
        TenantService.add_member(tenant.id, 20, TENANT_ROLE_MEMBER, 10)
