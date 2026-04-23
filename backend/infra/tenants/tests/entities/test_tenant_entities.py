import pytest

from infra.common.classes import MembershipRoles
from infra.common.exceptions import UnprocessableEntity
from infra.tenants.entities.tenant_entities import (
    TenantEntity,
    TenantMembershipEntity,
)


def test_tenant_entity_normalizes_name_and_slug():
    tenant = TenantEntity(name="  Acme Corp  ", slug="  Acme-Corp  ")

    assert tenant.name == "Acme Corp"
    assert tenant.slug == "acme-corp"


def test_tenant_entity_rejects_blank_name():
    with pytest.raises(UnprocessableEntity):
        TenantEntity(name="   ", slug="acme")


def test_tenant_entity_rejects_too_long_name():
    with pytest.raises(UnprocessableEntity):
        TenantEntity(name="x" * 201, slug="acme")


def test_tenant_entity_rejects_blank_slug():
    with pytest.raises(UnprocessableEntity):
        TenantEntity(name="Acme Corp", slug="   ")


def test_tenant_entity_rejects_too_long_slug():
    with pytest.raises(UnprocessableEntity):
        TenantEntity(name="Acme Corp", slug="a" * 101)


def test_tenant_entity_rejects_leading_hyphen_slug():
    with pytest.raises(UnprocessableEntity):
        TenantEntity(name="Acme Corp", slug="-invalid")


def test_tenant_entity_rejects_trailing_hyphen_slug():
    with pytest.raises(UnprocessableEntity):
        TenantEntity(name="Acme Corp", slug="invalid-")


def test_tenant_entity_rejects_uppercase_symbols_in_slug():
    with pytest.raises(UnprocessableEntity):
        TenantEntity(name="Acme Corp", slug="UPPER_")


def test_tenant_entity_accepts_single_alnum_slug():
    tenant = TenantEntity(name="Acme Corp", slug="a")

    assert tenant.slug == "a"


def test_tenant_entity_rejects_single_non_alnum_slug():
    with pytest.raises(UnprocessableEntity):
        TenantEntity(name="Acme Corp", slug="-")


def test_tenant_entity_accepts_numeric_slug_segments():
    tenant = TenantEntity(name="Acme Corp", slug="acme-123")

    assert tenant.slug == "acme-123"


def test_tenant_membership_entity_accepts_valid_role():
    membership = TenantMembershipEntity(role=MembershipRoles.ADMIN.value)

    assert membership.role == MembershipRoles.ADMIN.value


def test_tenant_membership_entity_rejects_invalid_role():
    with pytest.raises(UnprocessableEntity, match="Invalid role"):
        TenantMembershipEntity(role="guest")
