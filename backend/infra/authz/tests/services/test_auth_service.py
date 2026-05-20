from datetime import timedelta

import pytest
from django.utils import timezone

from infra.authz.dtos.auth_dtos import AuthToken, AuthUser, ClientContext
from infra.authz.services.auth_service import AuthService, get_auth_security_settings
from infra.common.exceptions import (
    NotFound,
    TooManyRequests,
    Unauthorized,
    UnprocessableEntity,
)


def make_user(
    user_id: int = 1,
    email: str = "user@example.com",
    password: str = "SecurePass123!",
    is_active: bool = True,
) -> AuthUser:
    return AuthUser(
        id=user_id,
        email=email,
        full_name="Test User",
        password_hash=AuthService._hash_password(password),
        is_active=is_active,
        created_at=timezone.now(),
    )


def make_client(ip: str = "127.0.0.1", user_agent: str = "pytest") -> ClientContext:
    return ClientContext(ip=ip, user_agent=user_agent)


def make_token(
    user: AuthUser,
    revoked_at=None,
    refresh_expires_at=None,
    family_id: str = "fam-1",
) -> AuthToken:
    now = timezone.now()
    return AuthToken(
        id=1,
        user=user,
        family_id=family_id,
        token_hash="token-hash",
        expires_at=now + timedelta(hours=1),
        refresh_token_hash="refresh-hash",
        refresh_expires_at=refresh_expires_at or now + timedelta(days=7),
        revoked_at=revoked_at,
        created_at=now,
        client_ip="127.0.0.1",
        user_agent="pytest",
    )


def patch_repo(monkeypatch, name: str, value) -> None:
    monkeypatch.setattr(
        f"infra.authz.repositories.auth_repository.AuthRepository.{name}",
        value,
    )


def stub_login_repo(monkeypatch, *, user: AuthUser | None) -> dict:
    state: dict = {
        "failed_logins": [],
        "events": [],
        "tokens_created": [],
        "revoked_old_sessions": 0,
    }

    patch_repo(monkeypatch, "find_user_by_email", lambda email: user)
    patch_repo(monkeypatch, "clear_stale_login_attempts", lambda before: 0)
    patch_repo(
        monkeypatch, "count_recent_failed_attempts_by_email", lambda email, since: 0
    )
    patch_repo(monkeypatch, "count_recent_failed_attempts_by_ip", lambda ip, since: 0)
    patch_repo(monkeypatch, "clear_failed_logins", lambda email: 1)
    patch_repo(
        monkeypatch,
        "record_failed_login",
        lambda email, ip: state["failed_logins"].append((email, ip)),
    )
    patch_repo(
        monkeypatch,
        "record_login_event",
        lambda **kwargs: state["events"].append(kwargs),
    )
    patch_repo(
        monkeypatch,
        "list_active_session_ids",
        lambda user_id, now: [],
    )
    patch_repo(
        monkeypatch,
        "revoke_tokens_by_ids",
        lambda token_ids, revoked_at: 0,
    )
    patch_repo(
        monkeypatch,
        "create_token",
        lambda **kwargs: state["tokens_created"].append(kwargs) or None,
    )
    return state


def test_register_user_rejects_weak_password():
    with pytest.raises(UnprocessableEntity):
        AuthService.register_user("user@example.com", "Test User", "password")


def test_register_user_rejects_invalid_email():
    with pytest.raises(UnprocessableEntity):
        AuthService.register_user("not-an-email", "Test User", "SecurePass123!")


def test_register_user_rejects_blank_full_name():
    with pytest.raises(UnprocessableEntity):
        AuthService.register_user("user@example.com", "   ", "SecurePass123!")


def test_login_rejects_blank_password():
    with pytest.raises(UnprocessableEntity):
        AuthService.login("user@example.com", "   ", make_client())


def test_login_creates_token_for_valid_credentials(monkeypatch):
    user = make_user()
    state = stub_login_repo(monkeypatch, user=user)

    session = AuthService.login("user@example.com", "SecurePass123!", make_client())

    assert session.user.email == "user@example.com"
    assert session.token_type == "bearer"
    assert session.expires_at > timezone.now()
    assert len(state["tokens_created"]) == 1
    assert state["tokens_created"][0]["family_id"]
    assert state["tokens_created"][0]["client_ip"] == "127.0.0.1"
    assert state["tokens_created"][0]["user_agent"] == "pytest"
    assert any(e["event_type"] == "login_success" for e in state["events"])


def test_login_records_failed_attempt_when_invalid_credentials(monkeypatch):
    user = make_user(password="SecurePass123!")
    state = stub_login_repo(monkeypatch, user=user)

    with pytest.raises(Unauthorized):
        AuthService.login("user@example.com", "wrong-password", make_client())

    assert state["failed_logins"] == [("user@example.com", "127.0.0.1")]
    assert any(e["event_type"] == "login_failure" for e in state["events"])


def test_login_does_not_record_failed_attempt_for_unknown_user(monkeypatch):
    state = stub_login_repo(monkeypatch, user=None)

    with pytest.raises(Unauthorized):
        AuthService.login("ghost@example.com", "any-password", make_client())

    assert state["failed_logins"] == []
    assert any(e["event_type"] == "login_failure" for e in state["events"])


def test_login_rejects_rate_limited_requests(monkeypatch):
    auth_settings = get_auth_security_settings()
    events: list[dict] = []

    patch_repo(monkeypatch, "clear_stale_login_attempts", lambda before: 0)
    patch_repo(
        monkeypatch,
        "count_recent_failed_attempts_by_email",
        lambda email, since: auth_settings.max_failed_attempts_per_account,
    )
    patch_repo(monkeypatch, "count_recent_failed_attempts_by_ip", lambda ip, since: 0)
    patch_repo(
        monkeypatch, "record_login_event", lambda **kwargs: events.append(kwargs)
    )

    with pytest.raises(TooManyRequests):
        AuthService.login("user@example.com", "SecurePass123!", make_client())

    assert any(e["event_type"] == "rate_limited" for e in events)


def test_authenticate_returns_none_for_invalid_token(monkeypatch):
    patch_repo(monkeypatch, "find_valid_token", lambda token_hash, now: None)

    assert AuthService.authenticate("invalid-token") is None


def test_authenticate_returns_user_for_valid_token(monkeypatch):
    user = make_user()
    token = make_token(user=user)

    patch_repo(monkeypatch, "find_valid_token", lambda token_hash, now: token)

    assert AuthService.authenticate("valid-token") == user


def test_logout_revokes_token(monkeypatch):
    revoked_tokens: list[str] = []
    user = make_user()
    token = make_token(user=user)

    patch_repo(monkeypatch, "find_valid_token", lambda token_hash, now: token)
    patch_repo(
        monkeypatch,
        "revoke_token",
        lambda token_hash, revoked_at: revoked_tokens.append(token_hash) or 1,
    )
    patch_repo(monkeypatch, "record_login_event", lambda **kwargs: None)

    AuthService.logout("valid-token")

    assert len(revoked_tokens) == 1


def test_refresh_rotates_token_and_keeps_family(monkeypatch):
    user = make_user()
    token = make_token(user=user, family_id="family-x")
    revoked_tokens: list[str] = []
    created_tokens: list[dict] = []

    patch_repo(monkeypatch, "find_token_by_refresh_hash", lambda h: token)
    patch_repo(
        monkeypatch,
        "revoke_token",
        lambda token_hash, revoked_at: revoked_tokens.append(token_hash) or 1,
    )
    patch_repo(
        monkeypatch,
        "create_token",
        lambda **kwargs: created_tokens.append(kwargs) or None,
    )
    patch_repo(monkeypatch, "record_login_event", lambda **kwargs: None)

    session = AuthService.refresh("refresh-token", make_client())

    assert session.user.id == user.id
    assert revoked_tokens == [token.token_hash]
    assert created_tokens[0]["family_id"] == "family-x"


def test_refresh_detects_reuse_and_revokes_family(monkeypatch):
    user = make_user()
    revoked_token = make_token(
        user=user,
        family_id="family-x",
        revoked_at=timezone.now(),
    )
    revoked_families: list[str] = []
    events: list[dict] = []

    patch_repo(monkeypatch, "find_token_by_refresh_hash", lambda h: revoked_token)
    patch_repo(
        monkeypatch,
        "revoke_token_family",
        lambda family_id, revoked_at: revoked_families.append(family_id) or 1,
    )
    patch_repo(
        monkeypatch, "record_login_event", lambda **kwargs: events.append(kwargs)
    )

    with pytest.raises(Unauthorized):
        AuthService.refresh("stolen-refresh", make_client())

    assert revoked_families == ["family-x"]
    assert any(e["event_type"] == "refresh_reuse" for e in events)


def test_refresh_rejects_unknown_token(monkeypatch):
    patch_repo(monkeypatch, "find_token_by_refresh_hash", lambda h: None)

    with pytest.raises(Unauthorized):
        AuthService.refresh("unknown-refresh", make_client())


def test_refresh_rejects_expired_refresh(monkeypatch):
    user = make_user()
    expired = make_token(
        user=user,
        refresh_expires_at=timezone.now() - timedelta(seconds=1),
    )

    patch_repo(monkeypatch, "find_token_by_refresh_hash", lambda h: expired)

    with pytest.raises(Unauthorized):
        AuthService.refresh("expired-refresh", make_client())


def test_authenticate_returns_none_for_blank_token():
    assert AuthService.authenticate("   ") is None


def test_authenticate_returns_none_for_empty_token():
    assert AuthService.authenticate("") is None


def test_authenticate_returns_none_for_inactive_user(monkeypatch):
    user = make_user(is_active=False)
    token = make_token(user=user)

    patch_repo(monkeypatch, "find_valid_token", lambda token_hash, now: token)

    assert AuthService.authenticate("valid-token") is None


def test_logout_is_noop_for_blank_token(monkeypatch):
    revoked: list[str] = []
    patch_repo(
        monkeypatch,
        "revoke_token",
        lambda token_hash, revoked_at: revoked.append(token_hash) or 1,
    )
    patch_repo(monkeypatch, "find_valid_token", lambda token_hash, now: None)

    AuthService.logout("   ")

    assert revoked == []


def test_logout_does_not_record_event_when_token_unknown(monkeypatch):
    events: list[dict] = []
    patch_repo(monkeypatch, "find_valid_token", lambda token_hash, now: None)
    patch_repo(monkeypatch, "revoke_token", lambda token_hash, revoked_at: 0)
    patch_repo(monkeypatch, "record_login_event", lambda **kw: events.append(kw))

    AuthService.logout("ghost-token")

    assert events == []


def test_refresh_rejects_blank_token():
    with pytest.raises(Unauthorized):
        AuthService.refresh("   ", make_client())


def test_refresh_rejects_inactive_user(monkeypatch):
    user = make_user(is_active=False)
    token = make_token(user=user)
    patch_repo(monkeypatch, "find_token_by_refresh_hash", lambda h: token)

    with pytest.raises(Unauthorized):
        AuthService.refresh("any-refresh", make_client())


def test_login_rate_limited_by_ip_attempts(monkeypatch):
    auth_settings = get_auth_security_settings()
    events: list[dict] = []

    patch_repo(monkeypatch, "clear_stale_login_attempts", lambda before: 0)
    patch_repo(
        monkeypatch, "count_recent_failed_attempts_by_email", lambda email, since: 0
    )
    patch_repo(
        monkeypatch,
        "count_recent_failed_attempts_by_ip",
        lambda ip, since: auth_settings.max_failed_attempts_per_ip,
    )
    patch_repo(
        monkeypatch, "record_login_event", lambda **kwargs: events.append(kwargs)
    )

    with pytest.raises(TooManyRequests):
        AuthService.login("user@example.com", "SecurePass123!", make_client())

    assert any(e["event_type"] == "rate_limited" for e in events)


def test_login_with_inactive_user_treated_as_invalid(monkeypatch):
    user = make_user(is_active=False)
    state = stub_login_repo(monkeypatch, user=user)

    with pytest.raises(Unauthorized):
        AuthService.login("user@example.com", "SecurePass123!", make_client())

    # Inactive users should NOT have failed-login attempts recorded against them.
    assert state["failed_logins"] == []
    assert any(e["event_type"] == "login_failure" for e in state["events"])


def test_update_user_name_succeeds(monkeypatch):
    user = make_user()
    received: dict = {}

    def fake_update(entity):
        received["entity"] = entity
        return user.model_copy(update={"full_name": entity.full_name.value})

    patch_repo(monkeypatch, "find_user_by_id", lambda user_id: user)
    patch_repo(monkeypatch, "update_user_name", fake_update)

    updated = AuthService.update_user_name(user.id, "  Renamed User  ")

    assert updated.full_name == "Renamed User"
    assert received["entity"].user_id == user.id
    assert received["entity"].full_name.value == "Renamed User"


def test_update_user_name_rejects_blank(monkeypatch):
    user = make_user()
    patch_repo(monkeypatch, "find_user_by_id", lambda user_id: user)

    with pytest.raises(UnprocessableEntity):
        AuthService.update_user_name(user.id, "   ")


def test_update_user_name_raises_not_found(monkeypatch):
    patch_repo(monkeypatch, "find_user_by_id", lambda user_id: None)

    with pytest.raises(NotFound):
        AuthService.update_user_name(99, "Whoever")


def test_update_user_email_succeeds(monkeypatch):
    user = make_user()
    received: dict = {}

    def fake_update(entity):
        received["entity"] = entity
        return user.model_copy(update={"email": entity.email.value})

    patch_repo(monkeypatch, "find_user_by_id", lambda user_id: user)
    patch_repo(monkeypatch, "update_user_email", fake_update)

    updated = AuthService.update_user_email(user.id, "  NEW@example.com ")

    assert updated.email == "new@example.com"
    assert received["entity"].email.value == "new@example.com"


def test_update_user_email_rejects_invalid_email(monkeypatch):
    user = make_user()
    patch_repo(monkeypatch, "find_user_by_id", lambda user_id: user)

    with pytest.raises(UnprocessableEntity):
        AuthService.update_user_email(user.id, "not-an-email")


def test_update_user_email_raises_not_found(monkeypatch):
    patch_repo(monkeypatch, "find_user_by_id", lambda user_id: None)

    with pytest.raises(NotFound):
        AuthService.update_user_email(99, "new@example.com")


def test_update_user_password_rejects_wrong_current_password(monkeypatch):
    user = make_user(password="SecurePass123!")
    patch_repo(monkeypatch, "find_user_by_id", lambda user_id: user)

    with pytest.raises(Unauthorized):
        AuthService.update_user_password(user.id, "wrong-current", "AnotherPass456!")


def test_update_user_password_rejects_weak_new_password(monkeypatch):
    user = make_user(password="SecurePass123!")
    patch_repo(monkeypatch, "find_user_by_id", lambda user_id: user)

    with pytest.raises(UnprocessableEntity):
        AuthService.update_user_password(user.id, "SecurePass123!", "password")


def test_update_user_password_raises_not_found(monkeypatch):
    patch_repo(monkeypatch, "find_user_by_id", lambda user_id: None)

    with pytest.raises(NotFound):
        AuthService.update_user_password(99, "anything", "AnotherPass456!")


def test_update_user_password_succeeds_with_valid_inputs(monkeypatch):
    user = make_user(password="SecurePass123!")
    captured: dict = {}

    def fake_update(entity):
        captured["entity"] = entity
        return user.model_copy(update={"password_hash": entity.new_password_hash})

    patch_repo(monkeypatch, "find_user_by_id", lambda user_id: user)
    patch_repo(monkeypatch, "update_user_password", fake_update)

    updated = AuthService.update_user_password(
        user.id, "SecurePass123!", "AnotherPass456!"
    )

    assert updated.password_hash == captured["entity"].new_password_hash
    assert AuthService._verify_password(
        "AnotherPass456!", captured["entity"].new_password_hash
    )


def test_rotate_session_after_password_change_revokes_all_and_issues_new(monkeypatch):
    user = make_user()
    revoked: list[int] = []
    created: list[dict] = []

    patch_repo(
        monkeypatch,
        "revoke_all_user_tokens",
        lambda user_id, revoked_at: revoked.append(user_id) or 3,
    )
    patch_repo(
        monkeypatch,
        "create_token",
        lambda **kwargs: created.append(kwargs) or None,
    )

    session = AuthService.rotate_session_after_password_change(user, make_client())

    assert revoked == [user.id]
    assert len(created) == 1
    assert session.user.id == user.id
    assert session.access_token
    assert session.refresh_token


def test_hash_token_is_deterministic_and_changes_with_input():
    a = AuthService._hash_token("abc")
    a_again = AuthService._hash_token("abc")
    b = AuthService._hash_token("abd")

    assert a == a_again
    assert a != b
    assert len(a) == 64  # sha256 hex digest


def test_normalize_client_ip_falls_back_to_unknown():
    assert AuthService._normalize_client_ip("") == "unknown"
    assert AuthService._normalize_client_ip("   ") == "unknown"


def test_normalize_client_ip_strips_whitespace():
    assert AuthService._normalize_client_ip("  10.0.0.1  ") == "10.0.0.1"


def test_normalize_user_agent_truncates_to_max_length():
    long_ua = "x" * 500

    result = AuthService._normalize_user_agent(long_ua)

    assert len(result) == 255


def test_normalize_user_agent_handles_blank():
    assert AuthService._normalize_user_agent("") == ""
    assert AuthService._normalize_user_agent("   ") == ""


def test_verify_password_returns_false_for_invalid_hash():
    # check_password raises TypeError/ValueError for malformed hashes; the
    # service catches both and returns False rather than propagating.
    assert AuthService._verify_password("any-pass", "not-a-real-hash") is False
