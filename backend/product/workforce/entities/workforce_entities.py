import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from infra.common.exceptions import UnprocessableEntity


@dataclass(frozen=True, slots=True)
class DepartmentEntity:
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", self._validate_name(self.name))

    @staticmethod
    def _validate_name(value: str) -> str:
        clean = value.strip()
        if not clean:
            raise UnprocessableEntity("Department name cannot be blank.")
        if len(clean) > 200:
            raise UnprocessableEntity("Department name cannot exceed 200 characters.")
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
            raise UnprocessableEntity("Role name cannot be blank.")
        if len(clean) > 200:
            raise UnprocessableEntity("Role name cannot exceed 200 characters.")
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
            raise UnprocessableEntity("Employee full name cannot be blank.")
        if len(clean) > 200:
            raise UnprocessableEntity(
                "Employee full name cannot exceed 200 characters."
            )
        return clean

    @staticmethod
    def _validate_email(value: str) -> str:
        clean = value.strip().lower()
        _EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
        if not _EMAIL_RE.match(clean):
            raise UnprocessableEntity(f"Invalid email address: '{value}'.")
        return clean


@dataclass(frozen=True, slots=True)
class DepartmentUpdateEntity:
    department_id: int
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", DepartmentEntity._validate_name(self.name))


@dataclass(frozen=True, slots=True)
class RoleUpdateEntity:
    role_id: int
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", RoleEntity._validate_name(self.name))


@dataclass(frozen=True, slots=True)
class EmployeeUpdateEntity:
    employee_id: int
    full_name: str
    email: str
    hired_at: date

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "full_name", EmployeeEntity._validate_full_name(self.full_name)
        )
        object.__setattr__(self, "email", EmployeeEntity._validate_email(self.email))


@dataclass(frozen=True, slots=True)
class SetEmployeeManagerEntity:
    employee_id: int
    manager_id: int | None


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
            raise UnprocessableEntity("Hourly rate must be greater than zero.")
        return value

    @staticmethod
    def _validate_contract_hours(value: int) -> int:
        if value <= 0 or value > 168:
            raise UnprocessableEntity(
                "Contract hours per week must be between 1 and 168."
            )
        return value


@dataclass(frozen=True, slots=True)
class CreateEmployeeEntity:
    full_name: str
    email: str
    hired_at: date
    department_id: int
    role_id: int
    hourly_rate: Decimal
    contract_hours_per_week: int
    user_id: int | None = None
    manager_id: int | None = None
    is_department_manager: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "full_name", EmployeeEntity._validate_full_name(self.full_name)
        )
        object.__setattr__(self, "email", EmployeeEntity._validate_email(self.email))
        object.__setattr__(
            self,
            "hourly_rate",
            EmployeeRoleEntity._validate_hourly_rate(self.hourly_rate),
        )
        object.__setattr__(
            self,
            "contract_hours_per_week",
            EmployeeRoleEntity._validate_contract_hours(self.contract_hours_per_week),
        )


@dataclass(frozen=True, slots=True)
class AssignDepartmentManagerEntity:
    employee_id: int


@dataclass(frozen=True, slots=True)
class RemoveDepartmentManagerEntity:
    reason: str = ""


@dataclass(frozen=True, slots=True)
class AssignDepartmentEntity:
    department_id: int
    reason: str = ""


@dataclass(frozen=True, slots=True)
class AssignRoleEntity:
    role_id: int
    hourly_rate: Decimal
    contract_hours_per_week: int
    reason: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "hourly_rate",
            EmployeeRoleEntity._validate_hourly_rate(self.hourly_rate),
        )
        object.__setattr__(
            self,
            "contract_hours_per_week",
            EmployeeRoleEntity._validate_contract_hours(self.contract_hours_per_week),
        )
