import re
from dataclasses import dataclass

from infra.common.classes import MembershipRoles
from infra.common.http_exceptions import UnprocessableEntity

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
_VALID_ROLES = {role.value for role in MembershipRoles}


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
            raise UnprocessableEntity("Tenant name cannot be blank.")
        if len(clean) > 200:
            raise UnprocessableEntity("Tenant name cannot exceed 200 characters.")
        return clean

    @staticmethod
    def _validate_slug(value: str) -> str:
        slug = value.strip().lower()
        if not slug:
            raise UnprocessableEntity("Slug cannot be blank.")
        if len(slug) > 100:
            raise UnprocessableEntity("Slug cannot exceed 100 characters.")
        if len(slug) == 1:
            if not slug.isalnum():
                raise UnprocessableEntity(
                    "Slug must be lowercase alphanumeric, optionally with hyphens."
                )
            return slug
        if not _SLUG_RE.match(slug):
            raise UnprocessableEntity(
                "Slug must start and end with alphanumeric characters and contain only "
                "lowercase letters, digits, or hyphens."
            )
        return slug


@dataclass(frozen=True, slots=True)
class TenantMembershipEntity:
    role: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", self._validate_role(self.role))

    @staticmethod
    def _validate_role(value: str) -> str:
        if value not in _VALID_ROLES:
            raise UnprocessableEntity(
                f"Invalid role '{value}'. Must be one of: {', '.join(sorted(_VALID_ROLES))}."
            )
        return value
