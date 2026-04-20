import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from authz.repositories.auth_repository import AuthRepository
from authz.dtos.dtos import AuthSession

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 600_000
TOKEN_TTL_HOURS = 8


class AuthError(Exception):
    pass


class InvalidCredentialsError(AuthError):
    pass


class EmailAlreadyExistsError(AuthError):
    pass

class AuthService:
    @staticmethod
    def register_user(email: str, full_name: str, password: str) -> Any:
        normalized_email = email.strip().lower()
        clean_name = full_name.strip()

        existing_user = AuthRepository.find_user_by_email(normalized_email)
        if existing_user:
            raise EmailAlreadyExistsError("A user with this email already exists")

        password_hash = AuthService._hash_password(password)
        return AuthRepository.create_user(
            email=normalized_email,
            full_name=clean_name,
            password_hash=password_hash,
        )

    @staticmethod
    def login(email: str, password: str) -> AuthSession:
        normalized_email = email.strip().lower()
        user = AuthRepository.find_user_by_email(normalized_email)

        if not user or not user.is_active:
            raise InvalidCredentialsError("Invalid credentials")

        if not AuthService._verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid credentials")

        access_token = secrets.token_urlsafe(48)
        expires_at = datetime.now(tz=UTC) + timedelta(hours=TOKEN_TTL_HOURS)

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
    def authenticate(access_token: str) -> Any | None:
        if not access_token:
            return None
        
        token_record = AuthRepository.find_valid_token(AuthService._hash_token(access_token))
        if not token_record or not token_record.user.is_active:
            return None

        return token_record.user

    @staticmethod
    def logout(access_token: str) -> None:
        if access_token:
            AuthRepository.revoke_token(AuthService._hash_token(access_token))

    @staticmethod
    def _repository():
        from infra.authz.repositories.auth_repository import AuthRepository

        return AuthRepository

    @staticmethod
    def _hash_password(raw_password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            raw_password.encode("utf-8"),
            salt.encode("utf-8"),
            PBKDF2_ITERATIONS,
        ).hex()
        return f"pbkdf2_{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}${salt}${digest}"

    @staticmethod
    def _verify_password(raw_password: str, encoded_password: str) -> bool:
        try:
            algorithm, iterations_str, salt, expected_hash = encoded_password.split("$", 3)
            if algorithm != f"pbkdf2_{PBKDF2_ALGORITHM}":
                return False

            computed_hash = hashlib.pbkdf2_hmac(
                PBKDF2_ALGORITHM,
                raw_password.encode("utf-8"),
                salt.encode("utf-8"),
                int(iterations_str),
            ).hex()
            return hmac.compare_digest(computed_hash, expected_hash)
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
