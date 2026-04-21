from product.workforce.dtos.workforce_dtos import (
    Department,
    Employee,
    EmployeeDepartment,
    EmployeeRole,
    Role,
)


def to_department(model) -> Department:
    return Department(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_role(model) -> Role:
    return Role(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_employee(model) -> Employee:
    return Employee(
        id=model.id,
        tenant_id=model.tenant_id,
        user_id=model.user_id,
        full_name=model.full_name,
        email=model.email,
        is_active=model.is_active,
        hired_at=model.hired_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_employee_department(model) -> EmployeeDepartment:
    return EmployeeDepartment(
        id=model.id,
        employee_id=model.employee_id,
        department_id=model.department_id,
        assigned_at=model.assigned_at,
        left_at=model.left_at,
        left_reason=model.left_reason or None,
    )


def to_employee_role(model) -> EmployeeRole:
    return EmployeeRole(
        id=model.id,
        employee_id=model.employee_id,
        role_id=model.role_id,
        hourly_rate=model.hourly_rate,
        contract_hours_per_week=model.contract_hours_per_week,
        assigned_at=model.assigned_at,
        left_at=model.left_at,
        left_reason=model.left_reason or None,
    )
