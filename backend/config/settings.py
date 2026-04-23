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


SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-a9g6w35*pkp_q0%4op83%k8@zr=(_a@-ipn%5y1hwv0-(+df*n",
)
DEBUG = env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "*")

INSTALLED_APPS = [
    "config",
    # product
    "product.workforce",
    "product.timekeeping",
    "product.costing",
    "product.approvals",
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

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "Europe/Madrid")

USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
