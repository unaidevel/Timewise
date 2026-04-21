from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Department:
    id: int
    tenant_id: int
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Role:
    id: int
    tenant_id: int
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Employee:
    id: int
    tenant_id: int
    user_id: int | None
    full_name: str
    email: str
    is_active: bool
    hired_at: date
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class EmployeeDepartment:
    id: int
    employee_id: int
    department_id: int
    assigned_at: datetime
    left_at: datetime | None
    left_reason: str | None


@dataclass(frozen=True, slots=True)
class EmployeeRole:
    id: int
    employee_id: int
    role_id: int
    hourly_rate: Decimal
    contract_hours_per_week: int
    assigned_at: datetime
    left_at: datetime | None
    left_reason: str | None
