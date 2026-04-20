import pytest

from infra.authz.entities.auth_entities import Email, FullName, Password
from infra.common.exceptions import (
    InvalidEmailError,
    InvalidFullNameError,
    InvalidPasswordError,
)


def test_email_normalizes_and_validates():
    email = Email("  USER@example.com  ")

    assert email.value == "user@example.com"


def test_email_rejects_invalid_values():
    with pytest.raises(InvalidEmailError):
        Email("invalid-email")


def test_full_name_trims_value():
    full_name = FullName("  Test User  ")

    assert full_name.value == "Test User"


def test_full_name_rejects_blank_value():
    with pytest.raises(InvalidFullNameError):
        FullName("   ")


def test_password_rejects_blank_value():
    with pytest.raises(InvalidPasswordError):
        Password("   ")
