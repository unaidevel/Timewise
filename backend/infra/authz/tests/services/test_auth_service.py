from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from infra.authz.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
)


def make_user(email: str = "user@example.com", is_active: bool = True):
    return SimpleNamespace(
        id=uuid4(),
        email=email,
        full_name="Test User",
        is_active=is_active,
        created_at=datetime.now(tz=UTC),
        password_hash="",
    )


def test_register_user_raises_if_email_exists(monkeypatch):
    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.find_user_by_email",
        lambda email: make_user(),
    )

    with pytest.raises(EmailAlreadyExistsError):
        AuthService.register_user("user@example.com", "Test User", "Secret123!")


def test_login_creates_token_for_valid_credentials(monkeypatch):
    password = "Secret123!"
    encoded_password = AuthService._hash_password(password)
    user = make_user()
    user.password_hash = encoded_password

    created_tokens: list[tuple[str, datetime]] = []

    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.find_user_by_email",
        lambda email: user,
    )
    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.create_token",
        lambda user, token_hash, expires_at: created_tokens.append((token_hash, expires_at)),
    )

    session = AuthService.login("user@example.com", password)

    assert session.user.email == "user@example.com"
    assert session.token_type == "bearer"
    assert session.expires_at > datetime.now(tz=UTC) + timedelta(hours=7)
    assert len(created_tokens) == 1


def test_login_fails_with_invalid_password(monkeypatch):
    user = make_user()
    user.password_hash = AuthService._hash_password("valid-password")

    monkeypatch.setattr(
        "infra.authz.repositories.auth_repository.AuthRepository.find_user_by_email",
        lambda email: user,
    )

    with pytest.raises(InvalidCredentialsError):
        AuthService.login("user@example.com", "wrong-password")
