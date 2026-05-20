from datetime import datetime

from django.db import IntegrityError

from infra.authz.dtos.auth_dtos import AuthToken, AuthUser
from infra.authz.entities.auth_entities import (
    UpdateUserEmailEntity,
    UpdateUserNameEntity,
    UpdateUserPasswordEntity,
)
from infra.authz.models import (
    AuthLoginAttemptModel,
    AuthLoginEventModel,
    AuthTokenModel,
    AuthUserModel,
)
from infra.common.exceptions import Conflict


class AuthRepository:
    @staticmethod
    def find_user_by_email(email: str) -> AuthUser | None:
        user_model = AuthUserModel.objects.filter(email=email).first()
        return AuthUser.model_validate(user_model) if user_model else None

    @staticmethod
    def find_user_by_id(user_id: int) -> AuthUser | None:
        user_model = AuthUserModel.objects.filter(id=user_id).first()
        return AuthUser.model_validate(user_model) if user_model else None

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

        return AuthUser.model_validate(user_model)

    @staticmethod
    def update_user_name(entity: UpdateUserNameEntity) -> AuthUser:
        if not isinstance(entity, UpdateUserNameEntity):
            raise TypeError(
                f"Expected UpdateUserNameEntity, got {type(entity).__name__}"
            )
        model = AuthUserModel(id=entity.user_id, full_name=entity.full_name.value)
        model.save(update_fields=["full_name", "updated_at"])
        return AuthUser.model_validate(AuthUserModel.objects.get(id=entity.user_id))

    @staticmethod
    def update_user_email(entity: UpdateUserEmailEntity) -> AuthUser:
        if not isinstance(entity, UpdateUserEmailEntity):
            raise TypeError(
                f"Expected UpdateUserEmailEntity, got {type(entity).__name__}"
            )
        try:
            model = AuthUserModel(id=entity.user_id, email=entity.email.value)
            model.save(update_fields=["email", "updated_at"])
        except IntegrityError as exc:
            raise Conflict("A user with this email already exists") from exc
        return AuthUser.model_validate(AuthUserModel.objects.get(id=entity.user_id))

    @staticmethod
    def update_user_password(entity: UpdateUserPasswordEntity) -> AuthUser:
        if not isinstance(entity, UpdateUserPasswordEntity):
            raise TypeError(
                f"Expected UpdateUserPasswordEntity, got {type(entity).__name__}"
            )
        model = AuthUserModel(id=entity.user_id, password_hash=entity.new_password_hash)
        model.save(update_fields=["password_hash", "updated_at"])
        return AuthUser.model_validate(AuthUserModel.objects.get(id=entity.user_id))

    @staticmethod
    def revoke_all_user_tokens(user_id: int, revoked_at: datetime) -> int:
        return AuthTokenModel.objects.filter(
            user_id=user_id, revoked_at__isnull=True
        ).update(revoked_at=revoked_at)

    @staticmethod
    def revoke_token_family(family_id: str, revoked_at: datetime) -> int:
        return AuthTokenModel.objects.filter(
            family_id=family_id, revoked_at__isnull=True
        ).update(revoked_at=revoked_at)

    @staticmethod
    def count_active_user_sessions(user_id: int, now: datetime) -> int:
        return AuthTokenModel.objects.filter(
            user_id=user_id,
            revoked_at__isnull=True,
            refresh_expires_at__gt=now,
        ).count()

    @staticmethod
    def list_active_session_ids(user_id: int, now: datetime) -> list[int]:
        return list(
            AuthTokenModel.objects.filter(
                user_id=user_id,
                revoked_at__isnull=True,
                refresh_expires_at__gt=now,
            )
            .order_by("-created_at")
            .values_list("id", flat=True)
        )

    @staticmethod
    def revoke_tokens_by_ids(token_ids: list[int], revoked_at: datetime) -> int:
        if not token_ids:
            return 0
        return AuthTokenModel.objects.filter(id__in=token_ids).update(
            revoked_at=revoked_at
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
        return AuthToken.model_validate(
            {
                "id": token_model.id,
                "user": user,
                "family_id": token_model.family_id,
                "token_hash": token_model.token_hash,
                "expires_at": token_model.expires_at,
                "refresh_token_hash": token_model.refresh_token_hash,
                "refresh_expires_at": token_model.refresh_expires_at,
                "revoked_at": token_model.revoked_at,
                "created_at": token_model.created_at,
                "client_ip": token_model.client_ip,
                "user_agent": token_model.user_agent,
            }
        )

    @staticmethod
    def find_valid_token(token_hash: str, now: datetime) -> AuthToken | None:
        token_model = (
            AuthTokenModel.objects.select_related("user")
            .filter(
                token_hash=token_hash,
                revoked_at__isnull=True,
                expires_at__gt=now,
            )
            .first()
        )
        return AuthToken.model_validate(token_model) if token_model else None

    @staticmethod
    def find_token_by_refresh_hash(refresh_token_hash: str) -> AuthToken | None:
        """Find a refresh token regardless of revocation status — needed for reuse detection."""
        token_model = (
            AuthTokenModel.objects.select_related("user")
            .filter(refresh_token_hash=refresh_token_hash)
            .first()
        )
        return AuthToken.model_validate(token_model) if token_model else None

    @staticmethod
    def revoke_token(token_hash: str, revoked_at: datetime) -> int:
        return AuthTokenModel.objects.filter(
            token_hash=token_hash, revoked_at__isnull=True
        ).update(revoked_at=revoked_at)

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
