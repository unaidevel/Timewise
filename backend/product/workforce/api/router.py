from fastapi import APIRouter, status

from infra.authz.api.dependencies import CurrentUser
from infra.common.http_exceptions import Conflict, Forbidden, NotFound, UnprocessableEntity
from infra.common.responses import responses_for
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
from product.workforce.services.workforce_service import WorkforceService

router = APIRouter(prefix="/api/v1/tenants/{tenant_id}", tags=["workforce"])


@router.post(
    "/departments",
    response_model=DepartmentOut,
    responses=responses_for(Conflict, UnprocessableEntity),
    status_code=status.HTTP_201_CREATED,
)
def create_department(
    tenant_id: int,
    payload: DepartmentIn,
    current_user: CurrentUser,
) -> DepartmentOut:
    return WorkforceService.create_department(tenant_id, payload, user_id=current_user.id)


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(tenant_id: int, _: CurrentUser) -> list[DepartmentOut]:
    return WorkforceService.list_departments(tenant_id)


@router.get(
    "/departments/{department_id}",
    response_model=DepartmentOut,
    responses=responses_for(NotFound),
)
def get_department(tenant_id: int, department_id: int, _: CurrentUser) -> DepartmentOut:
    return WorkforceService.get_department(tenant_id, department_id)


@router.delete(
    "/departments/{department_id}",
    response_model=DepartmentOut,
    responses=responses_for(NotFound),
)
def deactivate_department(
    tenant_id: int, department_id: int, current_user: CurrentUser
) -> DepartmentOut:
    return WorkforceService.deactivate_department(
        tenant_id, department_id, user_id=current_user.id
    )


@router.put(
    "/departments/{department_id}",
    response_model=DepartmentOut,
    responses=responses_for(Forbidden, NotFound, Conflict),
)
def update_department(
    tenant_id: int,
    department_id: int,
    payload: DepartmentUpdate,
    current_user: CurrentUser,
) -> DepartmentOut:
    return WorkforceService.update_department(
        tenant_id, department_id, payload, user_id=current_user.id
    )


@router.post(
    "/departments/{department_id}/managers",
    response_model=DepartmentManagerOut,
    responses=responses_for(Forbidden, NotFound, Conflict),
    status_code=status.HTTP_201_CREATED,
)
def assign_department_manager(
    tenant_id: int,
    department_id: int,
    payload: AssignDepartmentManagerRequest,
    current_user: CurrentUser,
) -> DepartmentManagerOut:
    return WorkforceService.assign_department_manager(
        tenant_id, department_id, payload, user_id=current_user.id
    )


@router.get(
    "/departments/{department_id}/managers",
    response_model=list[DepartmentManagerOut],
    responses=responses_for(NotFound),
)
def list_department_managers(
    tenant_id: int, department_id: int, _: CurrentUser
) -> list[DepartmentManagerOut]:
    return WorkforceService.list_department_managers(tenant_id, department_id)


@router.delete(
    "/departments/{department_id}/managers/{assignment_id}",
    response_model=DepartmentManagerOut,
    responses=responses_for(Forbidden, NotFound),
)
def remove_department_manager(
    tenant_id: int,
    department_id: int,
    assignment_id: int,
    payload: RemoveDepartmentManagerRequest,
    current_user: CurrentUser,
) -> DepartmentManagerOut:
    return WorkforceService.remove_department_manager(
        tenant_id, department_id, assignment_id, payload, user_id=current_user.id
    )


# --- Roles ---


@router.post(
    "/roles",
    response_model=RoleOut,
    responses=responses_for(Conflict, UnprocessableEntity),
    status_code=status.HTTP_201_CREATED,
)
def create_role(
    tenant_id: int,
    payload: RoleIn,
    current_user: CurrentUser,
) -> RoleOut:
    return WorkforceService.create_role(tenant_id, payload, user_id=current_user.id)


@router.get("/roles", response_model=list[RoleOut])
def list_roles(tenant_id: int, _: CurrentUser) -> list[RoleOut]:
    return WorkforceService.list_roles(tenant_id)


@router.get("/roles/{role_id}", response_model=RoleOut, responses=responses_for(NotFound))
def get_role(tenant_id: int, role_id: int, _: CurrentUser) -> RoleOut:
    return WorkforceService.get_role(tenant_id, role_id)


@router.delete(
    "/roles/{role_id}",
    response_model=RoleOut,
    responses=responses_for(NotFound),
)
def deactivate_role(
    tenant_id: int, role_id: int, current_user: CurrentUser
) -> RoleOut:
    return WorkforceService.deactivate_role(
        tenant_id, role_id, user_id=current_user.id
    )


@router.put(
    "/roles/{role_id}",
    response_model=RoleOut,
    responses=responses_for(Forbidden, NotFound, Conflict),
)
def update_role(
    tenant_id: int,
    role_id: int,
    payload: RoleUpdate,
    current_user: CurrentUser,
) -> RoleOut:
    return WorkforceService.update_role(
        tenant_id, role_id, payload, user_id=current_user.id
    )


@router.post(
    "/employees",
    response_model=EmployeeOut,
    responses=responses_for(NotFound, Conflict, UnprocessableEntity),
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    tenant_id: int,
    payload: EmployeeIn,
    current_user: CurrentUser,
) -> EmployeeOut:
    return WorkforceService.create_employee(
        tenant_id, payload, user_id=current_user.id
    )


@router.get("/employees", response_model=list[EmployeeOut])
def list_employees(tenant_id: int, _: CurrentUser) -> list[EmployeeOut]:
    return WorkforceService.list_employees(tenant_id)


@router.get(
    "/employees/{employee_id}",
    response_model=EmployeeOut,
    responses=responses_for(NotFound),
)
def get_employee(tenant_id: int, employee_id: int, _: CurrentUser) -> EmployeeOut:
    return WorkforceService.get_employee(tenant_id, employee_id)


@router.delete(
    "/employees/{employee_id}",
    response_model=EmployeeOut,
    responses=responses_for(NotFound),
)
def deactivate_employee(
    tenant_id: int, employee_id: int, current_user: CurrentUser
) -> EmployeeOut:
    return WorkforceService.deactivate_employee(
        tenant_id, employee_id, user_id=current_user.id
    )


@router.put(
    "/employees/{employee_id}",
    response_model=EmployeeOut,
    responses=responses_for(Forbidden, NotFound, Conflict, UnprocessableEntity),
)
def update_employee(
    tenant_id: int,
    employee_id: int,
    payload: EmployeeUpdate,
    current_user: CurrentUser,
) -> EmployeeOut:
    return WorkforceService.update_employee(
        tenant_id, employee_id, payload, user_id=current_user.id
    )


@router.put(
    "/employees/{employee_id}/manager",
    response_model=EmployeeOut,
    responses=responses_for(Forbidden, NotFound),
)
def set_employee_manager(
    tenant_id: int,
    employee_id: int,
    payload: SetEmployeeManagerRequest,
    current_user: CurrentUser,
) -> EmployeeOut:
    return WorkforceService.set_employee_manager(
        tenant_id, employee_id, payload, user_id=current_user.id
    )


@router.get(
    "/employees/{employee_id}/reports",
    response_model=list[EmployeeOut],
    responses=responses_for(NotFound),
)
def get_direct_reports(
    tenant_id: int, employee_id: int, _: CurrentUser
) -> list[EmployeeOut]:
    return WorkforceService.get_direct_reports(tenant_id, employee_id)


# --- Department assignments ---


@router.post(
    "/employees/{employee_id}/departments",
    response_model=EmployeeDepartmentOut,
    responses=responses_for(NotFound),
    status_code=status.HTTP_201_CREATED,
)
def assign_department(
    tenant_id: int,
    employee_id: int,
    payload: AssignDepartmentRequest,
    current_user: CurrentUser,
) -> EmployeeDepartmentOut:
    return WorkforceService.assign_department(
        tenant_id, employee_id, payload, user_id=current_user.id
    )


@router.get(
    "/employees/{employee_id}/departments/current",
    response_model=EmployeeDepartmentOut,
    responses=responses_for(NotFound),
)
def get_active_department(
    tenant_id: int, employee_id: int, _: CurrentUser
) -> EmployeeDepartmentOut:
    return WorkforceService.get_active_department(tenant_id, employee_id)


@router.get(
    "/employees/{employee_id}/departments",
    response_model=list[EmployeeDepartmentOut],
    responses=responses_for(NotFound),
)
def list_department_history(
    tenant_id: int, employee_id: int, _: CurrentUser
) -> list[EmployeeDepartmentOut]:
    return WorkforceService.list_department_history(tenant_id, employee_id)


@router.post(
    "/employees/{employee_id}/roles",
    response_model=EmployeeRoleOut,
    responses=responses_for(NotFound, UnprocessableEntity),
    status_code=status.HTTP_201_CREATED,
)
def assign_role(
    tenant_id: int,
    employee_id: int,
    payload: AssignRoleRequest,
    current_user: CurrentUser,
) -> EmployeeRoleOut:
    return WorkforceService.assign_role(
        tenant_id, employee_id, payload, user_id=current_user.id
    )


@router.get(
    "/employees/{employee_id}/roles/current",
    response_model=EmployeeRoleOut,
    responses=responses_for(NotFound),
)
def get_active_role(
    tenant_id: int, employee_id: int, _: CurrentUser
) -> EmployeeRoleOut:
    return WorkforceService.get_active_role(tenant_id, employee_id)


@router.get(
    "/employees/{employee_id}/roles",
    response_model=list[EmployeeRoleOut],
    responses=responses_for(NotFound),
)
def list_role_history(
    tenant_id: int, employee_id: int, _: CurrentUser
) -> list[EmployeeRoleOut]:
    return WorkforceService.list_role_history(tenant_id, employee_id)
