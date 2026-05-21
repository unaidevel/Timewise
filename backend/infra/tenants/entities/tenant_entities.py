import re
from dataclasses import dataclass

from infra.common.classes import ALLOWED_TIMEZONES, MembershipRoles
from infra.common.exceptions import UnprocessableEntity

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
_VALID_ROLES = {role.value for role in MembershipRoles}
_COUNTRY_RE = re.compile(r"^[A-Z]{2}$")
_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
_FISCAL_RE = re.compile(r"^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$")
_LOCALE_RE = re.compile(r"^[a-z]{2}(-[A-Z]{2})?$")


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
class TenantUpdateEntity:
    tenant_id: int
    name: str
    slug: str
    is_active: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", TenantEntity._validate_name(self.name))
        object.__setattr__(self, "slug", TenantEntity._validate_slug(self.slug))


@dataclass(frozen=True, slots=True)
class TenantMemberEntity:
    user_id: int
    role: str

    def __post_init__(self) -> None:
        if self.user_id <= 0:
            raise UnprocessableEntity("user_id must be a positive integer.")
        if self.role not in _VALID_ROLES:
            raise UnprocessableEntity(
                f"Invalid role '{self.role}'. Must be one of: {', '.join(sorted(_VALID_ROLES))}."
            )


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


@dataclass(frozen=True, slots=True)
class OrganizationProfileUpdateEntity:
    public_name: str
    legal_name: str
    workspace_name: str
    country: str
    timezone: str
    currency: str
    fiscal_year_start: str
    vat_number: str
    default_locale: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "public_name",
            self._validate_text(self.public_name, "public_name", 200),
        )
        object.__setattr__(
            self, "legal_name", self._validate_text(self.legal_name, "legal_name", 200)
        )
        object.__setattr__(
            self,
            "workspace_name",
            self._validate_text(self.workspace_name, "workspace_name", 100),
        )
        object.__setattr__(
            self, "vat_number", self._validate_text(self.vat_number, "vat_number", 32)
        )
        object.__setattr__(self, "country", self._validate_country(self.country))
        object.__setattr__(self, "timezone", self._validate_timezone(self.timezone))
        object.__setattr__(self, "currency", self._validate_currency(self.currency))
        object.__setattr__(
            self, "fiscal_year_start", self._validate_fiscal(self.fiscal_year_start)
        )
        object.__setattr__(
            self, "default_locale", self._validate_locale(self.default_locale)
        )

    @staticmethod
    def _validate_text(value: str, field: str, max_len: int) -> str:
        clean = (value or "").strip()
        if len(clean) > max_len:
            raise UnprocessableEntity(f"{field} cannot exceed {max_len} characters.")
        return clean

    @staticmethod
    def _validate_country(value: str) -> str:
        clean = (value or "").strip().upper()
        if clean and not _COUNTRY_RE.match(clean):
            raise UnprocessableEntity(
                "country must be a 2-letter ISO-3166 code (e.g. 'ES')."
            )
        return clean

    @staticmethod
    def _validate_timezone(value: str) -> str:
        clean = (value or "").strip()
        if not clean:
            return "UTC"
        if clean not in ALLOWED_TIMEZONES:
            raise UnprocessableEntity(
                f"timezone '{clean}' is not in the supported list."
            )
        return clean

    @staticmethod
    def _validate_currency(value: str) -> str:
        clean = (value or "").strip().upper()
        if not clean:
            return "EUR"
        if not _CURRENCY_RE.match(clean):
            raise UnprocessableEntity(
                "currency must be a 3-letter ISO-4217 code (e.g. 'EUR')."
            )
        return clean

    @staticmethod
    def _validate_fiscal(value: str) -> str:
        clean = (value or "").strip()
        if not clean:
            return "01-01"
        if not _FISCAL_RE.match(clean):
            raise UnprocessableEntity(
                "fiscal_year_start must be in MM-DD format (e.g. '01-01')."
            )
        return clean

    @staticmethod
    def _validate_locale(value: str) -> str:
        clean = (value or "").strip()
        if clean and not _LOCALE_RE.match(clean):
            raise UnprocessableEntity("default_locale must look like 'es' or 'es-ES'.")
        return clean
