import secrets
from dataclasses import dataclass
from datetime import timedelta
from functools import lru_cache
from hashlib import sha256
from types import SimpleNamespace

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from infra.authz.dtos.auth_dtos import AuthSession, AuthUser
from infra.authz.entities.auth_entities import Email, FullName, Password
from infra.authz.repositories.auth_repository import AuthRepository
from infra.common.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    TooManyLoginAttemptsError,
    WeakPasswordError,
)

STALE_LOGIN_ATTEMPT_RETENTION_DAYS = 30


@dataclass(frozen=True, slots=True)
class AuthSecuritySettings:
    token_ttl_hours: int
    max_failed_attempts_per_account: int
    max_failed_attempts_per_ip: int
    lockout_window_minutes: int


@lru_cache
def get_auth_security_settings() -> AuthSecuritySettings:
    return AuthSecuritySettings(
        token_ttl_hours=settings.AUTH_TOKEN_TTL_HOURS,
        max_failed_attempts_per_account=settings.AUTH_MAX_FAILED_ATTEMPTS_PER_ACCOUNT,
        max_failed_attempts_per_ip=settings.AUTH_MAX_FAILED_ATTEMPTS_PER_IP,
        lockout_window_minutes=settings.AUTH_LOCKOUT_WINDOW_MINUTES,
    )


class AuthService:
    @staticmethod
    def register_user(email: str, full_name: str, password: str) -> AuthUser:
        email_entity = Email(email)
        full_name_entity = FullName(full_name)
        password_entity = Password(password)

        existing_user = AuthRepository.find_user_by_email(email_entity.value)
        if existing_user:
            raise EmailAlreadyExistsError("A user with this email already exists")

        AuthService._validate_password(
            password_entity,
            email_entity,
            full_name_entity,
        )
        password_hash = AuthService._hash_password(password_entity.value)
        return AuthRepository.create_user(
            email=email_entity.value,
            full_name=full_name_entity.value,
            password_hash=password_hash,
        )

    @staticmethod
    def login(email: str, password: str, client_ip: str) -> AuthSession:
        auth_settings = get_auth_security_settings()
        email_entity = Email(email)
        password_entity = Password(password)
        normalized_ip = AuthService._normalize_client_ip(client_ip)

        AuthService._cleanup_stale_login_attempts()
        if AuthService._is_login_rate_limited(
            email_entity.value,
            normalized_ip,
            auth_settings,
        ):
            raise TooManyLoginAttemptsError("Too many login attempts. Try again later.")

        user = AuthRepository.find_user_by_email(email_entity.value)
        password_hash = (
            user.password_hash if user else AuthService._get_dummy_password_hash()
        )
        password_matches = AuthService._verify_password(
            password_entity.value,
            password_hash,
        )

        if not user or not user.is_active or not password_matches:
            AuthRepository.record_failed_login(email_entity.value, normalized_ip)
            raise InvalidCredentialsError("Invalid credentials")

        access_token = secrets.token_urlsafe(48)
        expires_at = timezone.now() + timedelta(hours=auth_settings.token_ttl_hours)

        AuthRepository.clear_failed_logins(email_entity.value)
        AuthRepository.create_token(
            user=user,
            token_hash=AuthService._hash_token(access_token),
            expires_at=expires_at,
        )

        return AuthSession(
            access_token=access_token,
            token_type="bearer",
            expires_at=expires_at,
            user=user,
        )

    @staticmethod
    def authenticate(access_token: str) -> AuthUser | None:
        clean_token = access_token.strip()
        if not clean_token:
            return None

        token_record = AuthRepository.find_valid_token(
            AuthService._hash_token(clean_token)
        )
        if not token_record or not token_record.user.is_active:
            return None

        return token_record.user

    @staticmethod
    def logout(access_token: str) -> None:
        clean_token = access_token.strip()
        if clean_token:
            AuthRepository.revoke_token(AuthService._hash_token(clean_token))

    @staticmethod
    def _hash_password(raw_password: str) -> str:
        return make_password(raw_password)

    @staticmethod
    def _verify_password(raw_password: str, encoded_password: str) -> bool:
        try:
            return check_password(raw_password, encoded_password)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return sha256(raw_token.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_client_ip(client_ip: str) -> str:
        clean_ip = (client_ip or "").strip()
        return clean_ip or "unknown"

    @staticmethod
    def _validate_password(
        password: Password,
        email: Email,
        full_name: FullName,
    ) -> None:
        first_name, _, last_name = full_name.value.partition(" ")
        validation_user = SimpleNamespace(
            username=email.value,
            email=email.value,
            first_name=first_name,
            last_name=last_name,
        )

        try:
            validate_password(password.value, user=validation_user)
        except DjangoValidationError as exc:
            raise WeakPasswordError(list(exc.messages)) from exc

    @staticmethod
    def _is_login_rate_limited(
        email: str,
        client_ip: str,
        auth_settings: AuthSecuritySettings,
    ) -> bool:
        window_start = timezone.now() - timedelta(
            minutes=auth_settings.lockout_window_minutes
        )
        account_attempts = AuthRepository.count_recent_failed_attempts_by_email(
            email,
            window_start,
        )
        ip_attempts = AuthRepository.count_recent_failed_attempts_by_ip(
            client_ip,
            window_start,
        )
        return (
            account_attempts >= auth_settings.max_failed_attempts_per_account
            or ip_attempts >= auth_settings.max_failed_attempts_per_ip
        )

    @staticmethod
    def _cleanup_stale_login_attempts() -> None:
        stale_before = timezone.now() - timedelta(
            days=STALE_LOGIN_ATTEMPT_RETENTION_DAYS
        )
        AuthRepository.clear_stale_login_attempts(stale_before)

    @staticmethod
    @lru_cache
    def _get_dummy_password_hash() -> str:
        return make_password("dummy-password-for-timing-protection")
