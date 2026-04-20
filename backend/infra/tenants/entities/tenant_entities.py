import re
from dataclasses import dataclass

from infra.tenants.exceptions import InvalidTenantNameError, InvalidTenantSlugError

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")


@dataclass(frozen=True, slots=True)
class TenantName:
    value: str

    def __post_init__(self) -> None:
        clean = self.value.strip()
        if not clean:
            raise InvalidTenantNameError("Tenant name cannot be blank.")
        if len(clean) > 200:
            raise InvalidTenantNameError("Tenant name cannot exceed 200 characters.")
        object.__setattr__(self, "value", clean)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class TenantSlug:
    value: str

    def __post_init__(self) -> None:
        slug = self.value.strip().lower()
        if not slug:
            raise InvalidTenantSlugError("Slug cannot be blank.")
        if len(slug) > 100:
            raise InvalidTenantSlugError("Slug cannot exceed 100 characters.")
        if len(slug) == 1:
            if not slug.isalnum():
                raise InvalidTenantSlugError(
                    "Slug must be lowercase alphanumeric, optionally with hyphens."
                )
        elif not _SLUG_RE.match(slug):
            raise InvalidTenantSlugError(
                "Slug must start and end with alphanumeric characters and contain only "
                "lowercase letters, digits, or hyphens."
            )
        object.__setattr__(self, "value", slug)

    def __str__(self) -> str:
        return self.value
