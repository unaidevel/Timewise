from datetime import timedelta

import pytest
from django.utils import timezone

from infra.authz.dtos.auth_dtos import AuthToken, AuthUser
from infra.authz.services.auth_service import AuthService, get_auth_security_settings
from infra.common.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidEmailError,
    InvalidFullNameError,
    InvalidPasswordError,
    TooManyLoginAttemptsError,
    WeakPasswordError,
)


def make_user(
    email: str = "user@example.com",
    password: str = "SecurePass123!",
    is_active: bool = True,
) -> AuthUser:
    return AuthUser(
        id=1,
        email=email,
        full_name="Test User",
        password_hash=AuthService._hash_password(password),
        is_active=is_active,
        created_at=timezone.now(),
    )


def test_register_user_raises_if_email_exists(monkeypatch):
    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.find_user_by_email",
        lambda email: make_user(),
    )

    with pytest.raises(EmailAlreadyExistsError):
        AuthService.register_user("user@example.com", "Test User", "SecurePass123!")


def test_register_user_rejects_weak_password():
    with pytest.raises(WeakPasswordError):
        AuthService.register_user("user@example.com", "Test User", "password")


def test_register_user_rejects_invalid_email():
    with pytest.raises(InvalidEmailError):
        AuthService.register_user("not-an-email", "Test User", "SecurePass123!")


def test_register_user_rejects_blank_full_name():
    with pytest.raises(InvalidFullNameError):
        AuthService.register_user("user@example.com", "   ", "SecurePass123!")


def test_login_rejects_blank_password():
    with pytest.raises(InvalidPasswordError):
        AuthService.login("user@example.com", "   ", "127.0.0.1")


def test_login_creates_token_for_valid_credentials(monkeypatch):
    user = make_user()
    created_tokens: list[tuple[str, timezone.datetime]] = []

    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.find_user_by_email",
        lambda email: user,
    )
    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.clear_stale_login_attempts",
        lambda before: 0,
    )
    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.count_recent_failed_attempts_by_email",
        lambda email, since: 0,
    )
    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.count_recent_failed_attempts_by_ip",
        lambda ip, since: 0,
    )
    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.clear_failed_logins",
        lambda email: 1,
    )
    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.create_token",
        lambda user, token_hash, expires_at: created_tokens.append(
            (token_hash, expires_at)
        ),
    )

    session = AuthService.login("user@example.com", "SecurePass123!", "127.0.0.1")

    assert session.user.email == "user@example.com"
    assert session.token_type == "bearer"
    assert session.expires_at > timezone.now() + timedelta(hours=7)
    assert len(created_tokens) == 1


def test_login_records_failed_attempt_when_invalid_credentials(monkeypatch):
    recorded_attempts: list[tuple[str, str]] = []
    user = make_user(password="SecurePass123!")

    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.find_user_by_email",
        lambda email: user,
    )
    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.clear_stale_login_attempts",
        lambda before: 0,
    )
    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.count_recent_failed_attempts_by_email",
        lambda email, since: 0,
    )
    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.count_recent_failed_attempts_by_ip",
        lambda ip, since: 0,
    )
    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.record_failed_login",
        lambda email, ip: recorded_attempts.append((email, ip)),
    )

    with pytest.raises(InvalidCredentialsError):
        AuthService.login("user@example.com", "wrong-password", "127.0.0.1")

    assert recorded_attempts == [("user@example.com", "127.0.0.1")]


def test_login_rejects_rate_limited_requests(monkeypatch):
    auth_settings = get_auth_security_settings()

    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.clear_stale_login_attempts",
        lambda before: 0,
    )
    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.count_recent_failed_attempts_by_email",
        lambda email, since: auth_settings.max_failed_attempts_per_account,
    )
    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.count_recent_failed_attempts_by_ip",
        lambda ip, since: 0,
    )

    with pytest.raises(TooManyLoginAttemptsError):
        AuthService.login("user@example.com", "SecurePass123!", "127.0.0.1")


def test_authenticate_returns_none_for_invalid_token(monkeypatch):
    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.find_valid_token",
        lambda token_hash: None,
    )

    assert AuthService.authenticate("invalid-token") is None


def test_authenticate_returns_user_for_valid_token(monkeypatch):
    user = make_user()
    token = AuthToken(
        id=1,
        user=user,
        token_hash="token-hash",
        expires_at=timezone.now() + timedelta(hours=1),
        revoked_at=None,
        created_at=timezone.now(),
    )

    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.find_valid_token",
        lambda token_hash: token,
    )

    assert AuthService.authenticate("valid-token") == user


def test_logout_revokes_token(monkeypatch):
    revoked_tokens: list[str] = []

    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.revoke_token",
        lambda token_hash: revoked_tokens.append(token_hash),
    )

    AuthService.logout("valid-token")

    assert len(revoked_tokens) == 1
