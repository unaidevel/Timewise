from datetime import datetime
from uuid import UUID

from django.utils import timezone

from infra.authz.models import AuthTokenModel, AuthUserModel


class AuthRepository:
    @staticmethod
    def find_user_by_email(email: str) -> AuthUserModel | None:
        return AuthUserModel.objects.filter(email=email).first()


    @staticmethod
    def find_user_by_id(user_id: UUID) -> AuthUserModel | None:
        return AuthUserModel.objects.filter(id=user_id).first()


    @staticmethod
    def create_user(email: str, full_name: str, password_hash: str) -> AuthUserModel:
        return AuthUserModel.objects.create(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
        )


    @staticmethod
    def create_token(
        user: AuthUserModel, token_hash: str, expires_at: datetime
    ) -> AuthTokenModel:
        return AuthTokenModel.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=expires_at,
        )


    @staticmethod
    def find_valid_token(token_hash: str) -> AuthTokenModel | None:
        return (
            AuthTokenModel.objects.select_related("user")
            .filter(
                token_hash=token_hash,
                revoked_at__isnull=True,
                expires_at__gt=timezone.now(),
            )
            .first()
        )


    @staticmethod
    def revoke_token(token_hash: str) -> int:
        return (
            AuthTokenModel.objects.filter(token_hash=token_hash, revoked_at__isnull=True)
            .update(revoked_at=timezone.now())
        )
