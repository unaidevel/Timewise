from dataclasses import dataclass

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email

from infra.common.http_exceptions import UnprocessableEntity


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized_email = self.value.strip().lower()
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
