from fastapi import APIRouter, HTTPException, status

from infra.authz.api.dependencies import CurrentUser
from infra.common.responses import STATUS_RESPONSES
from infra.tenants.exceptions import InsufficientPermissionsError
from product.workforce.dtos.dtos import (
    AssignDepartmentManagerRequest,
    AssignDepartmentRequest,
    AssignRoleRequest,
    DepartmentIn,
    DepartmentManagerOut,
    DepartmentOut,
    DepartmentUpdate,
    EmployeeDepartmentOut,
    EmployeeIn,
    EmployeeOut,
    EmployeeRoleOut,
    EmployeeUpdate,
    RemoveDepartmentManagerRequest,
    RoleIn,
    RoleOut,
    RoleUpdate,
    SetEmployeeManagerRequest,
)
from product.workforce.exceptions import (
    DepartmentAlreadyExistsError,
    DepartmentNotFoundError,
    EmployeeAlreadyExistsError,
    EmployeeNotFoundError,
    InvalidDepartmentNameError,
    InvalidEmployeeDataError,
    InvalidRoleNameError,
    ManagerAlreadyAssignedError,
    ManagerAssignmentNotFoundError,
    RoleAlreadyExistsError,
    RoleNotFoundError,
)
from product.workforce.services.workforce_service import WorkforceService

router = APIRouter(prefix="/api/v1/tenants/{tenant_id}", tags=["workforce"])


# --- Departments ---


@router.post(
    "/departments",
    response_model=DepartmentOut,
    responses=STATUS_RESPONSES,
    status_code=status.HTTP_201_CREATED,
)
def create_department(
    tenant_id: int,
    payload: DepartmentIn,
    _: CurrentUser,
) -> DepartmentOut:
    try:
        return WorkforceService.create_department(tenant_id, payload)
    except DepartmentAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except InvalidDepartmentNameError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(tenant_id: int, _: CurrentUser) -> list[DepartmentOut]:
    return WorkforceService.list_departments(tenant_id)


@router.get("/departments/{department_id}", response_model=DepartmentOut)
def get_department(tenant_id: int, department_id: int, _: CurrentUser) -> DepartmentOut:
    try:
        return WorkforceService.get_department(tenant_id, department_id)
    except DepartmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.delete("/departments/{department_id}", response_model=DepartmentOut)
def deactivate_department(
    tenant_id: int, department_id: int, _: CurrentUser
) -> DepartmentOut:
    try:
        return WorkforceService.deactivate_department(tenant_id, department_id)
    except DepartmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.patch("/departments/{department_id}", response_model=DepartmentOut)
def update_department(
    tenant_id: int,
    department_id: int,
    payload: DepartmentUpdate,
    current_user: CurrentUser,
) -> DepartmentOut:
    try:
        return WorkforceService.update_department(
            tenant_id, department_id, payload, user_id=current_user.id
        )
    except InsufficientPermissionsError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except DepartmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except (DepartmentAlreadyExistsError, InvalidDepartmentNameError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.post(
    "/departments/{department_id}/managers",
    response_model=DepartmentManagerOut,
    status_code=status.HTTP_201_CREATED,
)
def assign_department_manager(
    tenant_id: int,
    department_id: int,
    payload: AssignDepartmentManagerRequest,
    current_user: CurrentUser,
) -> DepartmentManagerOut:
    try:
        return WorkforceService.assign_department_manager(
            tenant_id, department_id, payload, user_id=current_user.id
        )
    except InsufficientPermissionsError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except (DepartmentNotFoundError, EmployeeNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ManagerAlreadyAssignedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.get(
    "/departments/{department_id}/managers",
    response_model=list[DepartmentManagerOut],
)
def list_department_managers(
    tenant_id: int, department_id: int, _: CurrentUser
) -> list[DepartmentManagerOut]:
    try:
        return WorkforceService.list_department_managers(tenant_id, department_id)
    except DepartmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.delete(
    "/departments/{department_id}/managers/{assignment_id}",
    response_model=DepartmentManagerOut,
)
def remove_department_manager(
    tenant_id: int,
    department_id: int,
    assignment_id: int,
    payload: RemoveDepartmentManagerRequest,
    current_user: CurrentUser,
) -> DepartmentManagerOut:
    try:
        return WorkforceService.remove_department_manager(
            tenant_id, department_id, assignment_id, payload, user_id=current_user.id
        )
    except InsufficientPermissionsError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except DepartmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ManagerAssignmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


# --- Roles ---


@router.post(
    "/roles",
    response_model=RoleOut,
    responses=STATUS_RESPONSES,
    status_code=status.HTTP_201_CREATED,
)
def create_role(tenant_id: int, payload: RoleIn, _: CurrentUser) -> RoleOut:
    try:
        return WorkforceService.create_role(tenant_id, payload)
    except RoleAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except InvalidRoleNameError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.get("/roles", response_model=list[RoleOut])
def list_roles(tenant_id: int, _: CurrentUser) -> list[RoleOut]:
    return WorkforceService.list_roles(tenant_id)


@router.get("/roles/{role_id}", response_model=RoleOut)
def get_role(tenant_id: int, role_id: int, _: CurrentUser) -> RoleOut:
    try:
        return WorkforceService.get_role(tenant_id, role_id)
    except RoleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.delete("/roles/{role_id}", response_model=RoleOut)
def deactivate_role(tenant_id: int, role_id: int, _: CurrentUser) -> RoleOut:
    try:
        return WorkforceService.deactivate_role(tenant_id, role_id)
    except RoleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.patch("/roles/{role_id}", response_model=RoleOut)
def update_role(
    tenant_id: int,
    role_id: int,
    payload: RoleUpdate,
    current_user: CurrentUser,
) -> RoleOut:
    try:
        return WorkforceService.update_role(
            tenant_id, role_id, payload, user_id=current_user.id
        )
    except InsufficientPermissionsError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except RoleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except (RoleAlreadyExistsError, InvalidRoleNameError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


# --- Employees ---


@router.post(
    "/employees",
    response_model=EmployeeOut,
    responses=STATUS_RESPONSES,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(tenant_id: int, payload: EmployeeIn, _: CurrentUser) -> EmployeeOut:
    try:
        return WorkforceService.create_employee(tenant_id, payload)
    except EmployeeAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except InvalidEmployeeDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except (DepartmentNotFoundError, RoleNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/employees", response_model=list[EmployeeOut])
def list_employees(tenant_id: int, _: CurrentUser) -> list[EmployeeOut]:
    return WorkforceService.list_employees(tenant_id)


@router.get("/employees/{employee_id}", response_model=EmployeeOut)
def get_employee(tenant_id: int, employee_id: int, _: CurrentUser) -> EmployeeOut:
    try:
        return WorkforceService.get_employee(tenant_id, employee_id)
    except EmployeeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.delete("/employees/{employee_id}", response_model=EmployeeOut)
def deactivate_employee(
    tenant_id: int, employee_id: int, _: CurrentUser
) -> EmployeeOut:
    try:
        return WorkforceService.deactivate_employee(tenant_id, employee_id)
    except EmployeeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.patch("/employees/{employee_id}", response_model=EmployeeOut)
def update_employee(
    tenant_id: int,
    employee_id: int,
    payload: EmployeeUpdate,
    current_user: CurrentUser,
) -> EmployeeOut:
    try:
        return WorkforceService.update_employee(
            tenant_id, employee_id, payload, user_id=current_user.id
        )
    except InsufficientPermissionsError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except EmployeeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except (EmployeeAlreadyExistsError, InvalidEmployeeDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.put("/employees/{employee_id}/manager", response_model=EmployeeOut)
def set_employee_manager(
    tenant_id: int,
    employee_id: int,
    payload: SetEmployeeManagerRequest,
    current_user: CurrentUser,
) -> EmployeeOut:
    try:
        return WorkforceService.set_employee_manager(
            tenant_id, employee_id, payload, user_id=current_user.id
        )
    except InsufficientPermissionsError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except EmployeeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/employees/{employee_id}/reports", response_model=list[EmployeeOut])
def get_direct_reports(
    tenant_id: int, employee_id: int, _: CurrentUser
) -> list[EmployeeOut]:
    try:
        return WorkforceService.get_direct_reports(tenant_id, employee_id)
    except EmployeeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


# --- Department assignments ---


@router.post(
    "/employees/{employee_id}/departments",
    response_model=EmployeeDepartmentOut,
    responses=STATUS_RESPONSES,
    status_code=status.HTTP_201_CREATED,
)
def assign_department(
    tenant_id: int,
    employee_id: int,
    payload: AssignDepartmentRequest,
    _: CurrentUser,
) -> EmployeeDepartmentOut:
    try:
        return WorkforceService.assign_department(tenant_id, employee_id, payload)
    except EmployeeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except DepartmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get(
    "/employees/{employee_id}/departments/current",
    response_model=EmployeeDepartmentOut,
)
def get_active_department(
    tenant_id: int, employee_id: int, _: CurrentUser
) -> EmployeeDepartmentOut:
    try:
        return WorkforceService.get_active_department(tenant_id, employee_id)
    except (EmployeeNotFoundError, DepartmentNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get(
    "/employees/{employee_id}/departments",
    response_model=list[EmployeeDepartmentOut],
)
def list_department_history(
    tenant_id: int, employee_id: int, _: CurrentUser
) -> list[EmployeeDepartmentOut]:
    try:
        return WorkforceService.list_department_history(tenant_id, employee_id)
    except EmployeeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


# --- Role assignments ---


@router.post(
    "/employees/{employee_id}/roles",
    response_model=EmployeeRoleOut,
    responses=STATUS_RESPONSES,
    status_code=status.HTTP_201_CREATED,
)
def assign_role(
    tenant_id: int,
    employee_id: int,
    payload: AssignRoleRequest,
    _: CurrentUser,
) -> EmployeeRoleOut:
    try:
        return WorkforceService.assign_role(tenant_id, employee_id, payload)
    except EmployeeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except (RoleNotFoundError, InvalidEmployeeDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get(
    "/employees/{employee_id}/roles/current",
    response_model=EmployeeRoleOut,
)
def get_active_role(
    tenant_id: int, employee_id: int, _: CurrentUser
) -> EmployeeRoleOut:
    try:
        return WorkforceService.get_active_role(tenant_id, employee_id)
    except (EmployeeNotFoundError, RoleNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get(
    "/employees/{employee_id}/roles",
    response_model=list[EmployeeRoleOut],
)
def list_role_history(
    tenant_id: int, employee_id: int, _: CurrentUser
) -> list[EmployeeRoleOut]:
    try:
        return WorkforceService.list_role_history(tenant_id, employee_id)
    except EmployeeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
