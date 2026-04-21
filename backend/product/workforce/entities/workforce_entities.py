import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from product.workforce.exceptions import (
    InvalidDepartmentNameError,
    InvalidEmployeeDataError,
    InvalidRoleNameError,
)

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


@dataclass(frozen=True, slots=True)
class DepartmentEntity:
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", self._validate_name(self.name))

    @staticmethod
    def _validate_name(value: str) -> str:
        clean = value.strip()
        if not clean:
            raise InvalidDepartmentNameError("Department name cannot be blank.")
        if len(clean) > 200:
            raise InvalidDepartmentNameError(
                "Department name cannot exceed 200 characters."
            )
        return clean


@dataclass(frozen=True, slots=True)
class RoleEntity:
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", self._validate_name(self.name))

    @staticmethod
    def _validate_name(value: str) -> str:
        clean = value.strip()
        if not clean:
            raise InvalidRoleNameError("Role name cannot be blank.")
        if len(clean) > 200:
            raise InvalidRoleNameError("Role name cannot exceed 200 characters.")
        return clean


@dataclass(frozen=True, slots=True)
class EmployeeEntity:
    full_name: str
    email: str
    hired_at: date

    def __post_init__(self) -> None:
        object.__setattr__(self, "full_name", self._validate_full_name(self.full_name))
        object.__setattr__(self, "email", self._validate_email(self.email))

    @staticmethod
    def _validate_full_name(value: str) -> str:
        clean = value.strip()
        if not clean:
            raise InvalidEmployeeDataError("Employee full name cannot be blank.")
        if len(clean) > 200:
            raise InvalidEmployeeDataError(
                "Employee full name cannot exceed 200 characters."
            )
        return clean

    @staticmethod
    def _validate_email(value: str) -> str:
        clean = value.strip().lower()
        if not _EMAIL_RE.match(clean):
            raise InvalidEmployeeDataError(f"Invalid email address: '{value}'.")
        return clean


@dataclass(frozen=True, slots=True)
class EmployeeRoleEntity:
    hourly_rate: Decimal
    contract_hours_per_week: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "hourly_rate", self._validate_hourly_rate(self.hourly_rate)
        )
        object.__setattr__(
            self,
            "contract_hours_per_week",
            self._validate_contract_hours(self.contract_hours_per_week),
        )

    @staticmethod
    def _validate_hourly_rate(value: Decimal) -> Decimal:
        if value <= Decimal("0"):
            raise InvalidEmployeeDataError("Hourly rate must be greater than zero.")
        return value

    @staticmethod
    def _validate_contract_hours(value: int) -> int:
        if value <= 0 or value > 168:
            raise InvalidEmployeeDataError(
                "Contract hours per week must be between 1 and 168."
            )
        return value
