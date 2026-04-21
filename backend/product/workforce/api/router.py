from fastapi import APIRouter, HTTPException, status

from infra.authz.api.dependencies import CurrentUser
from infra.common.responses import STATUS_RESPONSES
from product.workforce.dtos.dtos import (
    AssignDepartmentRequest,
    AssignRoleRequest,
    DepartmentIn,
    DepartmentOut,
    EmployeeDepartmentOut,
    EmployeeIn,
    EmployeeOut,
    EmployeeRoleOut,
    RoleIn,
    RoleOut,
)
from product.workforce.dtos.workforce_dtos import (
    Department,
    Employee,
    EmployeeDepartment,
    EmployeeRole,
    Role,
)
from product.workforce.exceptions import (
    DepartmentAlreadyExistsError,
    DepartmentNotFoundError,
    EmployeeAlreadyExistsError,
    EmployeeNotFoundError,
    InvalidDepartmentNameError,
    InvalidEmployeeDataError,
    InvalidRoleNameError,
    RoleAlreadyExistsError,
    RoleNotFoundError,
)
from product.workforce.services.workforce_service import WorkforceService

router = APIRouter(prefix="/api/v1/workforce", tags=["workforce"])


# --- Departments ---


@router.post(
    "/{tenant_id}/departments",
    response_model=DepartmentOut,
    responses=STATUS_RESPONSES,
    status_code=status.HTTP_201_CREATED,
)
def create_department(
    tenant_id: int,
    payload: DepartmentIn,
    _: CurrentUser,
) -> Department:
    try:
        return WorkforceService.create_department(tenant_id, payload)
    except DepartmentAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidDepartmentNameError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.get("/{tenant_id}/departments", response_model=list[DepartmentOut])
def list_departments(tenant_id: int, _: CurrentUser) -> list[Department]:
    return WorkforceService.list_departments(tenant_id)


@router.get("/{tenant_id}/departments/{department_id}", response_model=DepartmentOut)
def get_department(tenant_id: int, department_id: int, _: CurrentUser) -> Department:
    try:
        return WorkforceService.get_department(tenant_id, department_id)
    except DepartmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{tenant_id}/departments/{department_id}", response_model=DepartmentOut)
def deactivate_department(tenant_id: int, department_id: int, _: CurrentUser) -> Department:
    try:
        return WorkforceService.deactivate_department(tenant_id, department_id)
    except DepartmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# --- Roles ---


@router.post(
    "/{tenant_id}/roles",
    response_model=RoleOut,
    responses=STATUS_RESPONSES,
    status_code=status.HTTP_201_CREATED,
)
def create_role(tenant_id: int, payload: RoleIn, _: CurrentUser) -> Role:
    try:
        return WorkforceService.create_role(tenant_id, payload)
    except RoleAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidRoleNameError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.get("/{tenant_id}/roles", response_model=list[RoleOut])
def list_roles(tenant_id: int, _: CurrentUser) -> list[Role]:
    return WorkforceService.list_roles(tenant_id)


@router.get("/{tenant_id}/roles/{role_id}", response_model=RoleOut)
def get_role(tenant_id: int, role_id: int, _: CurrentUser) -> Role:
    try:
        return WorkforceService.get_role(tenant_id, role_id)
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{tenant_id}/roles/{role_id}", response_model=RoleOut)
def deactivate_role(tenant_id: int, role_id: int, _: CurrentUser) -> Role:
    try:
        return WorkforceService.deactivate_role(tenant_id, role_id)
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# --- Employees ---


@router.post(
    "/{tenant_id}/employees",
    response_model=EmployeeOut,
    responses=STATUS_RESPONSES,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(tenant_id: int, payload: EmployeeIn, _: CurrentUser) -> Employee:
    try:
        return WorkforceService.create_employee(tenant_id, payload)
    except EmployeeAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidEmployeeDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except (DepartmentNotFoundError, RoleNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{tenant_id}/employees", response_model=list[EmployeeOut])
def list_employees(tenant_id: int, _: CurrentUser) -> list[Employee]:
    return WorkforceService.list_employees(tenant_id)


@router.get("/{tenant_id}/employees/{employee_id}", response_model=EmployeeOut)
def get_employee(tenant_id: int, employee_id: int, _: CurrentUser) -> Employee:
    try:
        return WorkforceService.get_employee(tenant_id, employee_id)
    except EmployeeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{tenant_id}/employees/{employee_id}", response_model=EmployeeOut)
def deactivate_employee(tenant_id: int, employee_id: int, _: CurrentUser) -> Employee:
    try:
        return WorkforceService.deactivate_employee(tenant_id, employee_id)
    except EmployeeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# --- Department assignments ---


@router.post(
    "/{tenant_id}/employees/{employee_id}/departments",
    response_model=EmployeeDepartmentOut,
    responses=STATUS_RESPONSES,
    status_code=status.HTTP_201_CREATED,
)
def assign_department(
    tenant_id: int,
    employee_id: int,
    payload: AssignDepartmentRequest,
    _: CurrentUser,
) -> EmployeeDepartment:
    try:
        return WorkforceService.assign_department(tenant_id, employee_id, payload)
    except EmployeeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DepartmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{tenant_id}/employees/{employee_id}/departments/current",
    response_model=EmployeeDepartmentOut,
)
def get_active_department(
    tenant_id: int, employee_id: int, _: CurrentUser
) -> EmployeeDepartment:
    try:
        return WorkforceService.get_active_department(tenant_id, employee_id)
    except (EmployeeNotFoundError, DepartmentNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{tenant_id}/employees/{employee_id}/departments",
    response_model=list[EmployeeDepartmentOut],
)
def list_department_history(
    tenant_id: int, employee_id: int, _: CurrentUser
) -> list[EmployeeDepartment]:
    try:
        return WorkforceService.list_department_history(tenant_id, employee_id)
    except EmployeeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# --- Role assignments ---


@router.post(
    "/{tenant_id}/employees/{employee_id}/roles",
    response_model=EmployeeRoleOut,
    responses=STATUS_RESPONSES,
    status_code=status.HTTP_201_CREATED,
)
def assign_role(
    tenant_id: int,
    employee_id: int,
    payload: AssignRoleRequest,
    _: CurrentUser,
) -> EmployeeRole:
    try:
        return WorkforceService.assign_role(tenant_id, employee_id, payload)
    except EmployeeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (RoleNotFoundError, InvalidEmployeeDataError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{tenant_id}/employees/{employee_id}/roles/current",
    response_model=EmployeeRoleOut,
)
def get_active_role(tenant_id: int, employee_id: int, _: CurrentUser) -> EmployeeRole:
    try:
        return WorkforceService.get_active_role(tenant_id, employee_id)
    except (EmployeeNotFoundError, RoleNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{tenant_id}/employees/{employee_id}/roles",
    response_model=list[EmployeeRoleOut],
)
def list_role_history(
    tenant_id: int, employee_id: int, _: CurrentUser
) -> list[EmployeeRole]:
    try:
        return WorkforceService.list_role_history(tenant_id, employee_id)
    except EmployeeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
