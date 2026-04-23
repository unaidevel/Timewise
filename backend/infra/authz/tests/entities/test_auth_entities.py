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
