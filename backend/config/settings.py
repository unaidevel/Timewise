"""Django settings for a FastAPI project that still uses Django admin and ORM."""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(env_path: Path) -> None:
    """Load KEY=VALUE pairs from a simple .env file into os.environ."""
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


for candidate in (
    BASE_DIR / ".env",
    BASE_DIR / ".env" / "global.env",
    BASE_DIR / ".env" / "auth.env",
    BASE_DIR / ".env" / ".env",
    BASE_DIR / ".env" / ".env.local",
):
    load_env_file(candidate)


POSTGRES_DB_NAME = os.getenv("POSTGRES_DB", "timewise")
POSTGRES_TEST_DB_NAME = os.getenv("POSTGRES_TEST_DB", f"{POSTGRES_DB_NAME}_test")


def resolve_postgres_engine() -> str:
    engine = os.getenv("POSTGRES_ENGINE", "config.db.backends.postgresql")
    if engine == "django.db.backends.postgresql":
        return "config.db.backends.postgresql"
    return engine


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def env_int(name: str, default: int, minimum: int = 0) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        value = default
    else:
        try:
            value = int(raw_value)
        except ValueError as exc:
            raise ImproperlyConfigured(f"{name} must be an integer") from exc

    if value < minimum:
        raise ImproperlyConfigured(f"{name} must be >= {minimum}")

    return value


DEBUG = env_bool("DJANGO_DEBUG", True)

_INSECURE_DEV_SECRET_KEY = (
    "django-insecure-a9g6w35*pkp_q0%4op83%k8@zr=(_a@-ipn%5y1hwv0-(+df*n"
)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", _INSECURE_DEV_SECRET_KEY)

if not DEBUG and SECRET_KEY == _INSECURE_DEV_SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is False."
    )

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "*" if DEBUG else "")

if not DEBUG and (not ALLOWED_HOSTS or ALLOWED_HOSTS == ["*"]):
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS must list explicit hostnames when DJANGO_DEBUG is False."
    )

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000" if DEBUG else "",
)
CORS_ALLOWED_METHODS = env_list(
    "CORS_ALLOWED_METHODS",
    "GET,POST,PUT,PATCH,DELETE,OPTIONS",
)
CORS_ALLOWED_HEADERS = env_list(
    "CORS_ALLOWED_HEADERS",
    "Accept,Accept-Language,Content-Language,Content-Type,Authorization",
)

if not DEBUG and not CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured(
        "CORS_ALLOWED_ORIGINS must list explicit origins when DJANGO_DEBUG is False."
    )

RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")
RATE_LIMIT_AUTH = os.getenv("RATE_LIMIT_AUTH", "5/minute")
RATE_LIMIT_AUTHENTICATED = os.getenv("RATE_LIMIT_AUTHENTICATED", "1000/hour")

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = env_int("DJANGO_SECURE_HSTS_SECONDS", 31536000, minimum=0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
        "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", True
    )
    SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", True)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = "DENY"

INSTALLED_APPS = [
    "config",
    # product
    "product.workforce",
    "product.timekeeping",
    "product.costing",
    "product.approvals",
    "product.demo_data",
    # infra
    "infra.tenants",
    "infra.licensing",
    "infra.authz",
    # shared
    "shared.audit",
    "shared.notifications",
    "shared.common",
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": resolve_postgres_engine(),
        "NAME": POSTGRES_DB_NAME,
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "TEST": {
            "NAME": POSTGRES_TEST_DB_NAME,
            "MAINTENANCE_DB": os.getenv("POSTGRES_MAINTENANCE_DB", POSTGRES_DB_NAME),
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_ACCESS_TOKEN_TTL_MINUTES = env_int("AUTH_ACCESS_TOKEN_TTL_MINUTES", 15, minimum=1)
AUTH_REFRESH_TOKEN_TTL_DAYS = env_int("AUTH_REFRESH_TOKEN_TTL_DAYS", 5, minimum=1)
AUTH_MAX_FAILED_ATTEMPTS_PER_ACCOUNT = env_int(
    "AUTH_MAX_FAILED_ATTEMPTS_PER_ACCOUNT",
    5,
    minimum=1,
)
AUTH_MAX_FAILED_ATTEMPTS_PER_IP = env_int(
    "AUTH_MAX_FAILED_ATTEMPTS_PER_IP",
    20,
    minimum=1,
)
AUTH_LOCKOUT_WINDOW_MINUTES = env_int(
    "AUTH_LOCKOUT_WINDOW_MINUTES",
    15,
    minimum=1,
)
AUTH_MAX_ACTIVE_SESSIONS_PER_USER = env_int(
    "AUTH_MAX_ACTIVE_SESSIONS_PER_USER",
    5,
    minimum=1,
)
AUTH_TRUST_PROXY_HEADERS = env_bool("AUTH_TRUST_PROXY_HEADERS", False)
AUTH_TRUSTED_PROXIES = env_list("AUTH_TRUSTED_PROXIES", "")
AUTH_LOGIN_ATTEMPT_CLEANUP_PROBABILITY = env_int(
    "AUTH_LOGIN_ATTEMPT_CLEANUP_PROBABILITY_PCT",
    1,
    minimum=0,
)

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "Europe/Madrid")

USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


def _admin_link(label: str, icon: str, viewname: str) -> dict:
    from django.urls import reverse_lazy

    return {"title": label, "icon": icon, "link": reverse_lazy(viewname)}


UNFOLD = {
    "SITE_TITLE": "Timewise Admin",
    "SITE_HEADER": "Timewise",
    "SITE_SUBHEADER": "Internal administration",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Tenants & organisation",
                "separator": True,
                "items": [
                    _admin_link(
                        "Tenants", "domain", "admin:tenants_tenantmodel_changelist"
                    ),
                    _admin_link(
                        "Memberships",
                        "groups",
                        "admin:tenants_tenantmembershipmodel_changelist",
                    ),
                    _admin_link(
                        "Organisation profile",
                        "business",
                        "admin:tenants_organizationprofilemodel_changelist",
                    ),
                    _admin_link(
                        "Licensing",
                        "license",
                        "admin:licensing_licensisngmodel_changelist",
                    ),
                ],
            },
            {
                "title": "Workforce",
                "separator": True,
                "items": [
                    _admin_link(
                        "Employees",
                        "badge",
                        "admin:workforce_employeemodel_changelist",
                    ),
                    _admin_link(
                        "Departments",
                        "apartment",
                        "admin:workforce_departmentmodel_changelist",
                    ),
                    _admin_link(
                        "Roles", "work", "admin:workforce_rolemodel_changelist"
                    ),
                    _admin_link(
                        "Employee — department",
                        "person_pin",
                        "admin:workforce_employeedepartmentmodel_changelist",
                    ),
                    _admin_link(
                        "Employee — role",
                        "engineering",
                        "admin:workforce_employeerolemodel_changelist",
                    ),
                ],
            },
            {
                "title": "Time tracking",
                "separator": True,
                "items": [
                    _admin_link(
                        "Periods",
                        "calendar_month",
                        "admin:timekeeping_periodmodel_changelist",
                    ),
                    _admin_link(
                        "Time reports",
                        "description",
                        "admin:timekeeping_timereportmodel_changelist",
                    ),
                    _admin_link(
                        "Time entries",
                        "schedule",
                        "admin:timekeeping_timeentrymodel_changelist",
                    ),
                ],
            },
            {
                "title": "Costing",
                "separator": True,
                "items": [
                    _admin_link(
                        "Overtime rules",
                        "rule",
                        "admin:costing_overtimerulemodel_changelist",
                    ),
                    _admin_link(
                        "Rule conditions",
                        "tune",
                        "admin:costing_ruleconditionmodel_changelist",
                    ),
                    _admin_link(
                        "Cost calculations",
                        "calculate",
                        "admin:costing_costcalculationmodel_changelist",
                    ),
                ],
            },
            {
                "title": "Approvals",
                "separator": True,
                "items": [
                    _admin_link(
                        "Approvals",
                        "fact_check",
                        "admin:approvals_timereportapprovalmodel_changelist",
                    ),
                    _admin_link(
                        "Approval events",
                        "event_note",
                        "admin:approvals_timereportapprovaleventmodel_changelist",
                    ),
                ],
            },
            {
                "title": "Authentication",
                "separator": True,
                "items": [
                    _admin_link(
                        "Users", "person", "admin:authz_authusermodel_changelist"
                    ),
                    _admin_link(
                        "Refresh tokens",
                        "vpn_key",
                        "admin:authz_authtokenmodel_changelist",
                    ),
                    _admin_link(
                        "Login events",
                        "login",
                        "admin:authz_authlogineventmodel_changelist",
                    ),
                    _admin_link(
                        "Login attempts",
                        "lock_clock",
                        "admin:authz_authloginattemptmodel_changelist",
                    ),
                ],
            },
            {
                "title": "Audit & logs",
                "separator": True,
                "items": [
                    _admin_link(
                        "Audit events",
                        "fingerprint",
                        "admin:audit_auditeventmodel_changelist",
                    ),
                ],
            },
            {
                "title": "System",
                "separator": True,
                "items": [
                    _admin_link(
                        "Django users", "manage_accounts", "admin:auth_user_changelist"
                    ),
                    _admin_link(
                        "Django groups", "group", "admin:auth_group_changelist"
                    ),
                ],
            },
        ],
    },
}
