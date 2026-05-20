import secrets
from dataclasses import dataclass
from datetime import timedelta
from functools import lru_cache
from hashlib import sha256
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser

from infra.authz.dtos.auth_dtos import AuthSession, AuthUser, ClientContext
from infra.authz.entities.auth_entities import (
    Email,
    FullName,
    Password,
    UpdateUserEmailEntity,
    UpdateUserNameEntity,
    UpdateUserPasswordEntity,
)
from infra.authz.models import AuthLoginEventModel
from infra.authz.repositories.auth_repository import AuthRepository
from infra.common.exceptions import (
    NotFound,
    TooManyRequests,
    Unauthorized,
    UnprocessableEntity,
)

STALE_LOGIN_ATTEMPT_RETENTION_DAYS = 30
TOKEN_TYPE_BEARER = "bearer"  # nosec B105 - HTTP Authorization header prefix, not a credential
ACCESS_TOKEN_BYTES = 48
REFRESH_TOKEN_BYTES = 64
FAMILY_ID_BYTES = 32
USER_AGENT_MAX_LENGTH = 255


@dataclass(frozen=True, slots=True)
class AuthSecuritySettings:
    access_token_ttl_minutes: int
    refresh_token_ttl_days: int
    max_failed_attempts_per_account: int
    max_failed_attempts_per_ip: int
    lockout_window_minutes: int
    max_active_sessions_per_user: int
    cleanup_probability_pct: int


@lru_cache
def get_auth_security_settings() -> AuthSecuritySettings:
    return AuthSecuritySettings(
        access_token_ttl_minutes=settings.AUTH_ACCESS_TOKEN_TTL_MINUTES,
        refresh_token_ttl_days=settings.AUTH_REFRESH_TOKEN_TTL_DAYS,
        max_failed_attempts_per_account=settings.AUTH_MAX_FAILED_ATTEMPTS_PER_ACCOUNT,
        max_failed_attempts_per_ip=settings.AUTH_MAX_FAILED_ATTEMPTS_PER_IP,
        lockout_window_minutes=settings.AUTH_LOCKOUT_WINDOW_MINUTES,
        max_active_sessions_per_user=settings.AUTH_MAX_ACTIVE_SESSIONS_PER_USER,
        cleanup_probability_pct=settings.AUTH_LOGIN_ATTEMPT_CLEANUP_PROBABILITY,
    )


class AuthService:
    @staticmethod
    def register_user(email: str, full_name: str, password: str) -> AuthUser:
        email_entity = Email(email)
        full_name_entity = FullName(full_name)
        password_entity = Password(password)

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
    def update_user_name(user_id: int, full_name: str) -> AuthUser:
        if not AuthRepository.find_user_by_id(user_id):
            raise NotFound(f"User {user_id} not found.")
        entity = UpdateUserNameEntity(
            user_id=user_id,
            full_name=FullName(full_name),
        )
        return AuthRepository.update_user_name(entity)

    @staticmethod
    def update_user_email(user_id: int, email: str) -> AuthUser:
        if not AuthRepository.find_user_by_id(user_id):
            raise NotFound(f"User {user_id} not found.")
        entity = UpdateUserEmailEntity(
            user_id=user_id,
            email=Email(email),
        )
        return AuthRepository.update_user_email(entity)

    @staticmethod
    def update_user_password(
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> AuthUser:
        user = AuthRepository.find_user_by_id(user_id)
        if not user:
            raise NotFound(f"User {user_id} not found.")
        if not AuthService._verify_password(current_password, user.password_hash):
            raise Unauthorized("Current password is incorrect")
        new_password_entity = Password(new_password)
        AuthService._validate_password(
            new_password_entity,
            Email(user.email),
            FullName(user.full_name),
        )
        new_hash = AuthService._hash_password(new_password_entity.value)
        entity = UpdateUserPasswordEntity(
            user_id=user_id,
            new_password_hash=new_hash,
        )
        return AuthRepository.update_user_password(entity)

    @staticmethod
    def rotate_session_after_password_change(
        user: AuthUser,
        client: ClientContext,
    ) -> AuthSession:
        """Revoke every existing session for the user and issue a fresh one.

        Called after a password change so other devices are forced to log in
        again while the current request continues with a new access token.
        """
        AuthRepository.revoke_all_user_tokens(user.id, revoked_at=timezone.now())
        return AuthService._issue_session(
            user=user,
            family_id=AuthService._new_family_id(),
            auth_settings=get_auth_security_settings(),
            client_ip=AuthService._normalize_client_ip(client.ip),
            user_agent=AuthService._normalize_user_agent(client.user_agent),
        )

    @staticmethod
    def login(
        email: str,
        password: str,
        client: ClientContext,
    ) -> AuthSession:
        auth_settings = get_auth_security_settings()
        email_entity = Email(email)
        password_entity = Password(password)
        normalized_ip = AuthService._normalize_client_ip(client.ip)
        normalized_ua = AuthService._normalize_user_agent(client.user_agent)

        AuthService._maybe_cleanup_stale_login_attempts(auth_settings)
        if AuthService._is_login_rate_limited(
            email_entity.value,
            normalized_ip,
            auth_settings,
        ):
            AuthRepository.record_login_event(
                event_type=AuthLoginEventModel.EVENT_RATE_LIMITED,
                email=email_entity.value,
                client_ip=normalized_ip,
                user_agent=normalized_ua,
            )
            raise TooManyRequests("Too many login attempts. Try again later.")

        user = AuthRepository.find_user_by_email(email_entity.value)
        password_hash = (
            user.password_hash if user else AuthService._get_dummy_password_hash()
        )
        password_matches = AuthService._verify_password(
            password_entity.value,
            password_hash,
        )

        if not user or not user.is_active or not password_matches:
            if user and user.is_active:
                AuthRepository.record_failed_login(email_entity.value, normalized_ip)
            AuthRepository.record_login_event(
                event_type=AuthLoginEventModel.EVENT_LOGIN_FAILURE,
                user_id=user.id if user else None,
                email=email_entity.value,
                client_ip=normalized_ip,
                user_agent=normalized_ua,
            )
            raise Unauthorized("Invalid credentials")

        AuthRepository.clear_failed_logins(email_entity.value)
        now = timezone.now()
        active_ids = AuthRepository.list_active_session_ids(user.id, now=now)
        to_revoke = active_ids[auth_settings.max_active_sessions_per_user - 1 :]
        AuthRepository.revoke_tokens_by_ids(to_revoke, revoked_at=now)

        session = AuthService._issue_session(
            user=user,
            family_id=AuthService._new_family_id(),
            auth_settings=auth_settings,
            client_ip=normalized_ip,
            user_agent=normalized_ua,
        )
        AuthRepository.record_login_event(
            event_type=AuthLoginEventModel.EVENT_LOGIN_SUCCESS,
            user_id=user.id,
            email=email_entity.value,
            client_ip=normalized_ip,
            user_agent=normalized_ua,
        )
        return session

    @staticmethod
    def authenticate(access_token: str) -> AuthUser | None:
        clean_token = access_token.strip()
        if not clean_token:
            return None

        token_record = AuthRepository.find_valid_token(
            AuthService._hash_token(clean_token), now=timezone.now()
        )
        if not token_record or not token_record.user.is_active:
            return None

        return token_record.user

    @staticmethod
    def logout(access_token: str) -> None:
        clean_token = access_token.strip()
        if not clean_token:
            return

        token_hash = AuthService._hash_token(clean_token)
        now = timezone.now()
        token_record = AuthRepository.find_valid_token(token_hash, now=now)
        AuthRepository.revoke_token(token_hash, revoked_at=now)
        if token_record:
            AuthRepository.record_login_event(
                event_type=AuthLoginEventModel.EVENT_LOGOUT,
                user_id=token_record.user.id,
                email=token_record.user.email,
            )

    @staticmethod
    def refresh(refresh_token: str, client: ClientContext) -> AuthSession:
        clean_token = refresh_token.strip()
        if not clean_token:
            raise Unauthorized("Invalid or expired refresh token")

        normalized_ip = AuthService._normalize_client_ip(client.ip)
        normalized_ua = AuthService._normalize_user_agent(client.user_agent)
        token_record = AuthRepository.find_token_by_refresh_hash(
            AuthService._hash_token(clean_token)
        )

        if not token_record:
            raise Unauthorized("Invalid or expired refresh token")

        # Reuse detection: a previously-revoked refresh token being replayed
        # signals compromise. Revoke the entire token family.
        if token_record.revoked_at is not None:
            AuthRepository.revoke_token_family(
                token_record.family_id, revoked_at=timezone.now()
            )
            AuthRepository.record_login_event(
                event_type=AuthLoginEventModel.EVENT_REFRESH_REUSE,
                user_id=token_record.user.id,
                email=token_record.user.email,
                client_ip=normalized_ip,
                user_agent=normalized_ua,
            )
            raise Unauthorized("Invalid or expired refresh token")

        if (
            token_record.refresh_expires_at <= timezone.now()
            or not token_record.user.is_active
        ):
            raise Unauthorized("Invalid or expired refresh token")

        auth_settings = get_auth_security_settings()
        AuthRepository.revoke_token(token_record.token_hash, revoked_at=timezone.now())
        session = AuthService._issue_session(
            user=token_record.user,
            family_id=token_record.family_id,
            auth_settings=auth_settings,
            client_ip=normalized_ip,
            user_agent=normalized_ua,
        )
        AuthRepository.record_login_event(
            event_type=AuthLoginEventModel.EVENT_REFRESH,
            user_id=token_record.user.id,
            email=token_record.user.email,
            client_ip=normalized_ip,
            user_agent=normalized_ua,
        )
        return session

    @staticmethod
    def _issue_session(
        user: AuthUser,
        family_id: str,
        auth_settings: AuthSecuritySettings,
        client_ip: str,
        user_agent: str,
    ) -> AuthSession:
        access_token = secrets.token_urlsafe(ACCESS_TOKEN_BYTES)
        refresh_token = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
        now = timezone.now()
        expires_at = now + timedelta(minutes=auth_settings.access_token_ttl_minutes)
        refresh_expires_at = now + timedelta(days=auth_settings.refresh_token_ttl_days)

        AuthRepository.create_token(
            user=user,
            family_id=family_id,
            token_hash=AuthService._hash_token(access_token),
            expires_at=expires_at,
            refresh_token_hash=AuthService._hash_token(refresh_token),
            refresh_expires_at=refresh_expires_at,
            client_ip=client_ip,
            user_agent=user_agent,
        )

        return AuthSession(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=TOKEN_TYPE_BEARER,
            expires_at=expires_at,
            refresh_expires_at=refresh_expires_at,
            user=user,
        )

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
    def _new_family_id() -> str:
        return secrets.token_hex(FAMILY_ID_BYTES)

    @staticmethod
    def _normalize_client_ip(client_ip: str) -> str:
        clean_ip = (client_ip or "").strip()
        return clean_ip or "unknown"

    @staticmethod
    def _normalize_user_agent(user_agent: str) -> str:
        clean = (user_agent or "").strip()
        return clean[:USER_AGENT_MAX_LENGTH]

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
            # django-stubs types `user` as the concrete `User` model, but Django
            # itself accepts any object with the standard auth attributes.
            validate_password(
                password.value,
                user=cast("AbstractBaseUser", validation_user),  # type: ignore[arg-type]
            )
        except DjangoValidationError as exc:
            raise UnprocessableEntity(list(exc.messages)) from exc

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
        if account_attempts >= auth_settings.max_failed_attempts_per_account:
            return True
        ip_attempts = AuthRepository.count_recent_failed_attempts_by_ip(
            client_ip,
            window_start,
        )
        return ip_attempts >= auth_settings.max_failed_attempts_per_ip

    @staticmethod
    def _maybe_cleanup_stale_login_attempts(
        auth_settings: AuthSecuritySettings,
    ) -> None:
        if auth_settings.cleanup_probability_pct <= 0:
            return
        if secrets.randbelow(100) >= auth_settings.cleanup_probability_pct:
            return
        stale_before = timezone.now() - timedelta(
            days=STALE_LOGIN_ATTEMPT_RETENTION_DAYS
        )
        AuthRepository.clear_stale_login_attempts(stale_before)

    @staticmethod
    @lru_cache
    def _get_dummy_password_hash() -> str:
        return make_password("dummy-password-for-timing-protection")
