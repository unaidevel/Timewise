from dataclasses import dataclass

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email

from infra.common.exceptions import UnprocessableEntity

EMAIL_MAX_LENGTH = 254


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized_email = self.value.strip().lower()
        if len(normalized_email) > EMAIL_MAX_LENGTH:
            raise UnprocessableEntity("Email is too long.")
        try:
            validate_email(normalized_email)
        except DjangoValidationError as exc:
            raise UnprocessableEntity("Enter a valid email address.") from exc
        object.__setattr__(self, "value", normalized_email)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class FullName:
    value: str

    def __post_init__(self) -> None:
        clean_name = self.value.strip()
        if not clean_name:
            raise UnprocessableEntity("Full name cannot be blank.")
        object.__setattr__(self, "value", clean_name)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Password:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise UnprocessableEntity("Password cannot be blank.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class UpdateUserNameEntity:
    user_id: int
    full_name: FullName


@dataclass(frozen=True, slots=True)
class UpdateUserEmailEntity:
    user_id: int
    email: Email


@dataclass(frozen=True, slots=True)
class UpdateUserPasswordEntity:
    user_id: int
    new_password_hash: str
