import pytest

from infra.authz.entities.auth_entities import (
    Email,
    FullName,
    Password,
    Timezone,
    UpdateUserEmailEntity,
    UpdateUserNameEntity,
    UpdateUserPasswordEntity,
    UpdateUserTimezoneEntity,
)
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


def test_update_user_name_entity_holds_validated_full_name():
    entity = UpdateUserNameEntity(user_id=7, full_name=FullName("  New Name  "))

    assert entity.user_id == 7
    assert entity.full_name.value == "New Name"


def test_update_user_name_entity_is_frozen():
    entity = UpdateUserNameEntity(user_id=1, full_name=FullName("Test User"))

    with pytest.raises(AttributeError):
        entity.user_id = 2


def test_update_user_email_entity_holds_validated_email():
    entity = UpdateUserEmailEntity(user_id=3, email=Email("USER@example.com"))

    assert entity.user_id == 3
    assert entity.email.value == "user@example.com"


def test_update_user_email_entity_is_frozen():
    entity = UpdateUserEmailEntity(user_id=1, email=Email("user@example.com"))

    with pytest.raises(AttributeError):
        entity.email = Email("other@example.com")


def test_update_user_password_entity_stores_hash():
    entity = UpdateUserPasswordEntity(user_id=5, new_password_hash="hashed-value")

    assert entity.user_id == 5
    assert entity.new_password_hash == "hashed-value"


def test_update_user_password_entity_is_frozen():
    entity = UpdateUserPasswordEntity(user_id=1, new_password_hash="hashed")

    with pytest.raises(AttributeError):
        entity.new_password_hash = "other"


def test_timezone_accepts_none():
    tz = Timezone(None)

    assert tz.value is None


def test_timezone_treats_blank_as_none():
    tz = Timezone("   ")

    assert tz.value is None


def test_timezone_accepts_allowed_value():
    tz = Timezone("Europe/Madrid")

    assert tz.value == "Europe/Madrid"


def test_timezone_rejects_unknown_value():
    with pytest.raises(UnprocessableEntity, match="not in the supported list"):
        Timezone("Mars/Olympus")


def test_update_user_timezone_entity_holds_validated_timezone():
    entity = UpdateUserTimezoneEntity(user_id=4, timezone=Timezone("Europe/Madrid"))

    assert entity.user_id == 4
    assert entity.timezone.value == "Europe/Madrid"


def test_update_user_timezone_entity_supports_none():
    entity = UpdateUserTimezoneEntity(user_id=4, timezone=Timezone(None))

    assert entity.timezone.value is None
