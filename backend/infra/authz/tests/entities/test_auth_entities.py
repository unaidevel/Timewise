import pytest

from infra.authz.entities.auth_entities import Email, FullName, Password
from infra.common.exceptions import UnprocessableEntity


def test_email_normalizes_and_validates():
    email = Email("  USER@example.com  ")

    assert email.value == "user@example.com"


def test_email_rejects_invalid_values():
    with pytest.raises(UnprocessableEntity):
        Email("invalid-email")


def test_full_name_trims_value():
    full_name = FullName("  Test User  ")

    assert full_name.value == "Test User"


def test_full_name_rejects_blank_value():
    with pytest.raises(UnprocessableEntity):
        FullName("   ")


def test_password_rejects_blank_value():
    with pytest.raises(UnprocessableEntity):
        Password("   ")


def test_email_rejects_too_long_value():
    long_local_part = "a" * 250
    with pytest.raises(UnprocessableEntity, match="too long"):
        Email(f"{long_local_part}@example.com")


def test_email_rejects_blank_value():
    with pytest.raises(UnprocessableEntity):
        Email("   ")


def test_email_str_returns_value():
    email = Email("user@example.com")

    assert str(email) == "user@example.com"


def test_full_name_str_returns_value():
    full_name = FullName("Test User")

    assert str(full_name) == "Test User"


def test_password_rejects_empty_string():
    with pytest.raises(UnprocessableEntity):
        Password("")


def test_password_str_returns_value():
    password = Password("SecurePass123!")

    assert str(password) == "SecurePass123!"


def test_password_preserves_internal_whitespace():
    # Only outer blank-check matters; the value itself isn't trimmed.
    password = Password("  pass with spaces  ")

    assert password.value == "  pass with spaces  "


def test_email_is_frozen():
    email = Email("user@example.com")

    with pytest.raises(AttributeError):
        email.value = "other@example.com"
