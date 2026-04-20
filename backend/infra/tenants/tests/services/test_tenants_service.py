from uuid import uuid4

import pytest

from infra.tenants.dtos.tenant_dtos import Tenant, TenantMembership
from infra.tenants.exceptions import (
    MemberAlreadyExistsError,
    TenantAlreadyExistsError,
    TenantNotFoundError,
)
from infra.tenants.models import TENANT_ROLE_MEMBER, TENANT_ROLE_OWNER
from infra.tenants.services.tenants_service import TenantService
from django.utils import timezone


def make_tenant(slug: str = "acme") -> Tenant:
    return Tenant(
        id=uuid4(),
        name="Acme Corp",
        slug=slug,
        is_active=True,
        created_at=timezone.now(),
        created_by_id=uuid4(),
    )


def make_membership(tenant_id=None, user_id=None, role=TENANT_ROLE_OWNER) -> TenantMembership:
    return TenantMembership(
        id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        user_id=user_id or uuid4(),
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
        TenantService.create("Acme Corp", "acme", uuid4())


def test_create_tenant_raises_on_invalid_name():
    with pytest.raises(Exception):
        TenantService.create("", "acme", uuid4())


def test_create_tenant_raises_on_invalid_slug():
    with pytest.raises(Exception):
        TenantService.create("Acme Corp", "-invalid", uuid4())


def test_create_tenant_adds_owner_membership(monkeypatch):
    created_tenants = []
    added_memberships = []
    tenant = make_tenant()

    monkeypatch.setattr(
        "infra.tenants.services.tenants_service.TenantRepository.find_by_slug",
        lambda slug: None,
    )
    monkeypatch.setattr(
        "infra.tenants.services.tenants_service.TenantRepository.create",
        lambda name, slug, created_by_id: (created_tenants.append(slug), tenant)[1],
    )
    monkeypatch.setattr(
        "infra.tenants.services.tenants_service.TenantRepository.add_membership",
        lambda tenant_id, user_id, role, invited_by_id: added_memberships.append(role),
    )

    TenantService.create("Acme Corp", "acme", uuid4())

    assert added_memberships == [TENANT_ROLE_OWNER]


def test_get_by_id_raises_if_not_found(monkeypatch):
    monkeypatch.setattr(
        "infra.tenants.services.tenants_service.TenantRepository.find_by_id",
        lambda tenant_id: None,
    )

    with pytest.raises(TenantNotFoundError):
        TenantService.get_by_id(uuid4())


def test_add_member_raises_if_tenant_not_found(monkeypatch):
    monkeypatch.setattr(
        "infra.tenants.services.tenants_service.TenantRepository.find_by_id",
        lambda tenant_id: None,
    )

    with pytest.raises(TenantNotFoundError):
        TenantService.add_member(uuid4(), uuid4(), TENANT_ROLE_MEMBER, uuid4())


def test_add_member_raises_if_already_member(monkeypatch):
    tenant = make_tenant()
    membership = make_membership(tenant_id=tenant.id)

    monkeypatch.setattr(
        "infra.tenants.services.tenants_service.TenantRepository.find_by_id",
        lambda tenant_id: tenant,
    )
    monkeypatch.setattr(
        "infra.tenants.services.tenants_service.TenantRepository.find_active_membership",
        lambda tenant_id, user_id: membership,
    )

    with pytest.raises(MemberAlreadyExistsError):
        TenantService.add_member(tenant.id, uuid4(), TENANT_ROLE_MEMBER, uuid4())
