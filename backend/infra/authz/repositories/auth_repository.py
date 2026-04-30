from datetime import datetime

from django.db import IntegrityError
from django.utils import timezone

from infra.authz.dtos.auth_dtos import AuthToken, AuthUser
from infra.authz.models import (
    AuthLoginAttemptModel,
    AuthLoginEventModel,
    AuthTokenModel,
    AuthUserModel,
)
from infra.common.exceptions import Conflict


def _to_auth_user(user_model: AuthUserModel) -> AuthUser:
    return AuthUser(
        id=user_model.id,
        email=user_model.email,
        full_name=user_model.full_name,
        password_hash=user_model.password_hash,
        is_active=user_model.is_active,
        created_at=user_model.created_at,
    )


def _to_auth_token(token_model: AuthTokenModel) -> AuthToken:
    return AuthToken(
        id=token_model.id,
        user=_to_auth_user(token_model.user),
        family_id=token_model.family_id,
        token_hash=token_model.token_hash,
        expires_at=token_model.expires_at,
        refresh_token_hash=token_model.refresh_token_hash,
        refresh_expires_at=token_model.refresh_expires_at,
        revoked_at=token_model.revoked_at,
        created_at=token_model.created_at,
        client_ip=token_model.client_ip,
        user_agent=token_model.user_agent,
    )


class AuthRepository:
    @staticmethod
    def find_user_by_email(email: str) -> AuthUser | None:
        user_model = AuthUserModel.objects.filter(email=email).first()
        return _to_auth_user(user_model) if user_model else None

    @staticmethod
    def find_user_by_id(user_id: int) -> AuthUser | None:
        user_model = AuthUserModel.objects.filter(id=user_id).first()
        return _to_auth_user(user_model) if user_model else None

    @staticmethod
    def create_user(email: str, full_name: str, password_hash: str) -> AuthUser:
        try:
            user_model = AuthUserModel.objects.create(
                email=email,
                full_name=full_name,
                password_hash=password_hash,
            )
        except IntegrityError as exc:
            raise Conflict("A user with this email already exists") from exc

        return _to_auth_user(user_model)

    @staticmethod
    def revoke_all_user_tokens(user_id: int) -> int:
        return AuthTokenModel.objects.filter(
            user_id=user_id, revoked_at__isnull=True
        ).update(revoked_at=timezone.now())

    @staticmethod
    def revoke_token_family(family_id: str) -> int:
        return AuthTokenModel.objects.filter(
            family_id=family_id, revoked_at__isnull=True
        ).update(revoked_at=timezone.now())

    @staticmethod
    def count_active_user_sessions(user_id: int) -> int:
        return AuthTokenModel.objects.filter(
            user_id=user_id,
            revoked_at__isnull=True,
            refresh_expires_at__gt=timezone.now(),
        ).count()

    @staticmethod
    def revoke_oldest_active_user_sessions(user_id: int, keep: int) -> int:
        active_ids = list(
            AuthTokenModel.objects.filter(
                user_id=user_id,
                revoked_at__isnull=True,
                refresh_expires_at__gt=timezone.now(),
            )
            .order_by("-created_at")
            .values_list("id", flat=True)
        )
        to_revoke = active_ids[keep:]
        if not to_revoke:
            return 0
        return AuthTokenModel.objects.filter(id__in=to_revoke).update(
            revoked_at=timezone.now()
        )

    @staticmethod
    def create_token(
        user: AuthUser,
        family_id: str,
        token_hash: str,
        expires_at: datetime,
        refresh_token_hash: str,
        refresh_expires_at: datetime,
        client_ip: str = "",
        user_agent: str = "",
    ) -> AuthToken:
        token_model = AuthTokenModel.objects.create(
            user_id=user.id,
            family_id=family_id,
            token_hash=token_hash,
            expires_at=expires_at,
            refresh_token_hash=refresh_token_hash,
            refresh_expires_at=refresh_expires_at,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        return AuthToken(
            id=token_model.id,
            user=user,
            family_id=token_model.family_id,
            token_hash=token_model.token_hash,
            expires_at=token_model.expires_at,
            refresh_token_hash=token_model.refresh_token_hash,
            refresh_expires_at=token_model.refresh_expires_at,
            revoked_at=token_model.revoked_at,
            created_at=token_model.created_at,
            client_ip=token_model.client_ip,
            user_agent=token_model.user_agent,
        )

    @staticmethod
    def find_valid_token(token_hash: str) -> AuthToken | None:
        token_model = (
            AuthTokenModel.objects.select_related("user")
            .filter(
                token_hash=token_hash,
                revoked_at__isnull=True,
                expires_at__gt=timezone.now(),
            )
            .first()
        )
        return _to_auth_token(token_model) if token_model else None

    @staticmethod
    def find_token_by_refresh_hash(refresh_token_hash: str) -> AuthToken | None:
        """Find a refresh token regardless of revocation status — needed for reuse detection."""
        token_model = (
            AuthTokenModel.objects.select_related("user")
            .filter(refresh_token_hash=refresh_token_hash)
            .first()
        )
        return _to_auth_token(token_model) if token_model else None

    @staticmethod
    def revoke_token(token_hash: str) -> int:
        return AuthTokenModel.objects.filter(
            token_hash=token_hash, revoked_at__isnull=True
        ).update(revoked_at=timezone.now())

    @staticmethod
    def record_failed_login(email: str, ip_address: str) -> None:
        AuthLoginAttemptModel.objects.create(email=email, ip_address=ip_address)

    @staticmethod
    def count_recent_failed_attempts_by_email(email: str, since: datetime) -> int:
        return AuthLoginAttemptModel.objects.filter(
            email=email,
            attempted_at__gte=since,
        ).count()

    @staticmethod
    def count_recent_failed_attempts_by_ip(ip_address: str, since: datetime) -> int:
        return AuthLoginAttemptModel.objects.filter(
            ip_address=ip_address,
            attempted_at__gte=since,
        ).count()

    @staticmethod
    def clear_failed_logins(email: str) -> int:
        deleted_count, _ = AuthLoginAttemptModel.objects.filter(email=email).delete()
        return deleted_count

    @staticmethod
    def clear_stale_login_attempts(before: datetime) -> int:
        deleted_count, _ = AuthLoginAttemptModel.objects.filter(
            attempted_at__lt=before
        ).delete()
        return deleted_count

    @staticmethod
    def record_login_event(
        event_type: str,
        user_id: int | None = None,
        email: str = "",
        client_ip: str = "",
        user_agent: str = "",
    ) -> None:
        AuthLoginEventModel.objects.create(
            user_id=user_id,
            email=email,
            event_type=event_type,
            client_ip=client_ip,
            user_agent=user_agent,
        )
