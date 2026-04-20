import re
from dataclasses import dataclass

from infra.tenants.exceptions import InvalidTenantNameError, InvalidTenantSlugError

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")


@dataclass(frozen=True, slots=True)
class TenantEntity:
    name: str
    slug: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", self._validate_name(self.name))
        object.__setattr__(self, "slug", self._validate_slug(self.slug))

    @staticmethod
    def _validate_name(value: str) -> str:
        clean = value.strip()
        if not clean:
            raise InvalidTenantNameError("Tenant name cannot be blank.")
        if len(clean) > 200:
            raise InvalidTenantNameError("Tenant name cannot exceed 200 characters.")
        return clean

    @staticmethod
    def _validate_slug(value: str) -> str:
        slug = value.strip().lower()
        if not slug:
            raise InvalidTenantSlugError("Slug cannot be blank.")
        if len(slug) > 100:
            raise InvalidTenantSlugError("Slug cannot exceed 100 characters.")
        if len(slug) == 1:
            if not slug.isalnum():
                raise InvalidTenantSlugError(
                    "Slug must be lowercase alphanumeric, optionally with hyphens."
                )
            return slug
        if not _SLUG_RE.match(slug):
            raise InvalidTenantSlugError(
                "Slug must start and end with alphanumeric characters and contain only "
                "lowercase letters, digits, or hyphens."
            )
        return slug
