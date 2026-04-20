import pytest

from infra.tenants.entities.tenant_entities import TenantName, TenantSlug
from infra.tenants.exceptions import InvalidTenantNameError, InvalidTenantSlugError


def test_tenant_name_strips_and_accepts():
    name = TenantName("  Acme Corp  ")
    assert name.value == "Acme Corp"


def test_tenant_name_rejects_blank():
    with pytest.raises(InvalidTenantNameError):
        TenantName("   ")


def test_tenant_name_rejects_too_long():
    with pytest.raises(InvalidTenantNameError):
        TenantName("x" * 201)


def test_tenant_slug_lowercases_and_strips():
    slug = TenantSlug("  Acme-Corp  ")
    assert slug.value == "acme-corp"


def test_tenant_slug_rejects_blank():
    with pytest.raises(InvalidTenantSlugError):
        TenantSlug("   ")


def test_tenant_slug_rejects_too_long():
    with pytest.raises(InvalidTenantSlugError):
        TenantSlug("a" * 101)


def test_tenant_slug_rejects_leading_hyphen():
    with pytest.raises(InvalidTenantSlugError):
        TenantSlug("-invalid")


def test_tenant_slug_rejects_trailing_hyphen():
    with pytest.raises(InvalidTenantSlugError):
        TenantSlug("invalid-")


def test_tenant_slug_rejects_uppercase():
    with pytest.raises(InvalidTenantSlugError):
        TenantSlug("UPPER")


def test_tenant_slug_accepts_single_alnum():
    slug = TenantSlug("a")
    assert slug.value == "a"


def test_tenant_slug_accepts_numbers():
    slug = TenantSlug("acme-123")
    assert slug.value == "acme-123"
