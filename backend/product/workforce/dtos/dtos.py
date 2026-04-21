from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DepartmentIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RoleIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class EmployeeIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=254)
    department_id: int
    role_id: int
    hourly_rate: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    contract_hours_per_week: int = Field(ge=1, le=168)
    hired_at: date
    user_id: int | None = None


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    user_id: int | None
    full_name: str
    email: str
    is_active: bool
    hired_at: date
    created_at: datetime
    updated_at: datetime


class AssignDepartmentRequest(BaseModel):
    department_id: int
    reason: str = ""


class AssignRoleRequest(BaseModel):
    role_id: int
    hourly_rate: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    contract_hours_per_week: int = Field(ge=1, le=168)
    reason: str = ""


class EmployeeDepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    department_id: int
    assigned_at: datetime
    left_at: datetime | None
    left_reason: str | None


class EmployeeRoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    role_id: int
    hourly_rate: Decimal
    contract_hours_per_week: int
    assigned_at: datetime
    left_at: datetime | None
    left_reason: str | None
