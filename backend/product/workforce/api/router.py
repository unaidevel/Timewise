from fastapi import APIRouter, Request, status

from infra.authz.api.dependencies import RateLimitedUser
from infra.common.exceptions import (
    Conflict,
    Forbidden,
    NotFound,
    TooManyRequests,
    UnprocessableEntity,
    responses_for,
)
from infra.common.rate_limiting import USER_RATE_LIMIT, limiter, user_or_ip_key
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
    LinkEmployeeUserRequest,
    RemoveDepartmentManagerRequest,
    RoleIn,
    RoleOut,
    RoleUpdate,
    SetEmployeeManagerRequest,
)
from product.workforce.orchestrators.workforce_orchestrator import WorkforceOrchestrator
from product.workforce.services.workforce_service import WorkforceService

router = APIRouter(prefix="/api/v1/tenants/{tenant_id}", tags=["workforce"])


@router.post(
    "/departments",
    response_model=DepartmentOut,
    responses=responses_for(Conflict, UnprocessableEntity, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def create_department(
    tenant_id: int,
    payload: DepartmentIn,
    current_user: RateLimitedUser,
    request: Request,
) -> DepartmentOut:
    return WorkforceOrchestrator.create_department(
        tenant_id, payload, user_id=current_user.id
    )


@router.get(
    "/departments",
    response_model=list[DepartmentOut],
    responses=responses_for(TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_departments(
    tenant_id: int, _: RateLimitedUser, request: Request
) -> list[DepartmentOut]:
    return WorkforceService.list_departments(tenant_id)


@router.get(
    "/departments/{department_id}",
    response_model=DepartmentOut,
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def get_department(
    tenant_id: int, department_id: int, _: RateLimitedUser, request: Request
) -> DepartmentOut:
    return WorkforceService.get_department(tenant_id, department_id)


@router.delete(
    "/departments/{department_id}",
    response_model=DepartmentOut,
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def deactivate_department(
    tenant_id: int,
    department_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> DepartmentOut:
    return WorkforceOrchestrator.deactivate_department(
        tenant_id, department_id, user_id=current_user.id
    )


@router.put(
    "/departments/{department_id}",
    response_model=DepartmentOut,
    responses=responses_for(Forbidden, NotFound, Conflict, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def update_department(
    tenant_id: int,
    department_id: int,
    payload: DepartmentUpdate,
    current_user: RateLimitedUser,
    request: Request,
) -> DepartmentOut:
    return WorkforceOrchestrator.update_department(
        tenant_id, department_id, payload, user_id=current_user.id
    )


@router.post(
    "/departments/{department_id}/managers",
    response_model=DepartmentManagerOut,
    responses=responses_for(Forbidden, NotFound, Conflict, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def assign_department_manager(
    tenant_id: int,
    department_id: int,
    payload: AssignDepartmentManagerRequest,
    current_user: RateLimitedUser,
    request: Request,
) -> DepartmentManagerOut:
    return WorkforceOrchestrator.assign_department_manager(
        tenant_id, department_id, payload, user_id=current_user.id
    )


@router.get(
    "/departments/{department_id}/managers",
    response_model=list[DepartmentManagerOut],
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_department_managers(
    tenant_id: int, department_id: int, _: RateLimitedUser, request: Request
) -> list[DepartmentManagerOut]:
    return WorkforceService.list_department_managers(tenant_id, department_id)


@router.delete(
    "/departments/{department_id}/managers/{assignment_id}",
    response_model=DepartmentManagerOut,
    responses=responses_for(Forbidden, NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def remove_department_manager(
    tenant_id: int,
    department_id: int,
    assignment_id: int,
    payload: RemoveDepartmentManagerRequest,
    current_user: RateLimitedUser,
    request: Request,
) -> DepartmentManagerOut:
    return WorkforceOrchestrator.remove_department_manager(
        tenant_id, department_id, assignment_id, payload, user_id=current_user.id
    )


# --- Roles ---


@router.post(
    "/roles",
    response_model=RoleOut,
    responses=responses_for(Conflict, UnprocessableEntity, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def create_role(
    tenant_id: int,
    payload: RoleIn,
    current_user: RateLimitedUser,
    request: Request,
) -> RoleOut:
    return WorkforceOrchestrator.create_role(
        tenant_id, payload, user_id=current_user.id
    )


@router.get(
    "/roles",
    response_model=list[RoleOut],
    responses=responses_for(TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_roles(tenant_id: int, _: RateLimitedUser, request: Request) -> list[RoleOut]:
    return WorkforceService.list_roles(tenant_id)


@router.get(
    "/roles/{role_id}",
    response_model=RoleOut,
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def get_role(
    tenant_id: int, role_id: int, _: RateLimitedUser, request: Request
) -> RoleOut:
    return WorkforceService.get_role(tenant_id, role_id)


@router.delete(
    "/roles/{role_id}",
    response_model=RoleOut,
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def deactivate_role(
    tenant_id: int,
    role_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> RoleOut:
    return WorkforceOrchestrator.deactivate_role(
        tenant_id, role_id, user_id=current_user.id
    )


@router.put(
    "/roles/{role_id}",
    response_model=RoleOut,
    responses=responses_for(Forbidden, NotFound, Conflict, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def update_role(
    tenant_id: int,
    role_id: int,
    payload: RoleUpdate,
    current_user: RateLimitedUser,
    request: Request,
) -> RoleOut:
    return WorkforceOrchestrator.update_role(
        tenant_id, role_id, payload, user_id=current_user.id
    )


@router.post(
    "/employees",
    response_model=EmployeeOut,
    responses=responses_for(NotFound, Conflict, UnprocessableEntity, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def create_employee(
    tenant_id: int,
    payload: EmployeeIn,
    current_user: RateLimitedUser,
    request: Request,
) -> EmployeeOut:
    return WorkforceOrchestrator.create_employee(
        tenant_id, payload, user_id=current_user.id
    )


@router.get(
    "/employees",
    response_model=list[EmployeeOut],
    responses=responses_for(TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_employees(
    tenant_id: int, _: RateLimitedUser, request: Request
) -> list[EmployeeOut]:
    return WorkforceService.list_employees(tenant_id)


@router.get(
    "/employees/{employee_id}",
    response_model=EmployeeOut,
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def get_employee(
    tenant_id: int, employee_id: int, _: RateLimitedUser, request: Request
) -> EmployeeOut:
    return WorkforceService.get_employee(tenant_id, employee_id)


@router.delete(
    "/employees/{employee_id}",
    response_model=EmployeeOut,
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def deactivate_employee(
    tenant_id: int,
    employee_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> EmployeeOut:
    return WorkforceOrchestrator.deactivate_employee(
        tenant_id, employee_id, user_id=current_user.id
    )


@router.put(
    "/employees/{employee_id}",
    response_model=EmployeeOut,
    responses=responses_for(
        Forbidden, NotFound, Conflict, UnprocessableEntity, TooManyRequests
    ),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def update_employee(
    tenant_id: int,
    employee_id: int,
    payload: EmployeeUpdate,
    current_user: RateLimitedUser,
    request: Request,
) -> EmployeeOut:
    return WorkforceOrchestrator.update_employee(
        tenant_id, employee_id, payload, user_id=current_user.id
    )


@router.put(
    "/employees/{employee_id}/user",
    response_model=EmployeeOut,
    responses=responses_for(Forbidden, NotFound, Conflict, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def link_employee_user(
    tenant_id: int,
    employee_id: int,
    payload: LinkEmployeeUserRequest,
    current_user: RateLimitedUser,
    request: Request,
) -> EmployeeOut:
    return WorkforceOrchestrator.link_user(
        tenant_id, employee_id, payload, user_id=current_user.id
    )


@router.put(
    "/employees/{employee_id}/manager",
    response_model=EmployeeOut,
    responses=responses_for(Forbidden, NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def set_employee_manager(
    tenant_id: int,
    employee_id: int,
    payload: SetEmployeeManagerRequest,
    current_user: RateLimitedUser,
    request: Request,
) -> EmployeeOut:
    return WorkforceOrchestrator.set_employee_manager(
        tenant_id, employee_id, payload, user_id=current_user.id
    )


@router.get(
    "/employees/{employee_id}/reports",
    response_model=list[EmployeeOut],
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def get_direct_reports(
    tenant_id: int, employee_id: int, _: RateLimitedUser, request: Request
) -> list[EmployeeOut]:
    return WorkforceService.get_direct_reports(tenant_id, employee_id)


# --- Department assignments ---


@router.post(
    "/employees/{employee_id}/departments",
    response_model=EmployeeDepartmentOut,
    responses=responses_for(NotFound, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def assign_department(
    tenant_id: int,
    employee_id: int,
    payload: AssignDepartmentRequest,
    current_user: RateLimitedUser,
    request: Request,
) -> EmployeeDepartmentOut:
    return WorkforceOrchestrator.assign_department(
        tenant_id, employee_id, payload, user_id=current_user.id
    )


@router.get(
    "/employees/{employee_id}/departments/current",
    response_model=EmployeeDepartmentOut,
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def get_active_department(
    tenant_id: int, employee_id: int, _: RateLimitedUser, request: Request
) -> EmployeeDepartmentOut:
    return WorkforceService.get_active_department(tenant_id, employee_id)


@router.get(
    "/employees/{employee_id}/departments",
    response_model=list[EmployeeDepartmentOut],
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_department_history(
    tenant_id: int, employee_id: int, _: RateLimitedUser, request: Request
) -> list[EmployeeDepartmentOut]:
    return WorkforceService.list_department_history(tenant_id, employee_id)


@router.post(
    "/employees/{employee_id}/roles",
    response_model=EmployeeRoleOut,
    responses=responses_for(NotFound, UnprocessableEntity, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def assign_role(
    tenant_id: int,
    employee_id: int,
    payload: AssignRoleRequest,
    current_user: RateLimitedUser,
    request: Request,
) -> EmployeeRoleOut:
    return WorkforceOrchestrator.assign_role(
        tenant_id, employee_id, payload, user_id=current_user.id
    )


@router.get(
    "/employees/{employee_id}/roles/current",
    response_model=EmployeeRoleOut,
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def get_active_role(
    tenant_id: int, employee_id: int, _: RateLimitedUser, request: Request
) -> EmployeeRoleOut:
    return WorkforceService.get_active_role(tenant_id, employee_id)


@router.get(
    "/employees/{employee_id}/roles",
    response_model=list[EmployeeRoleOut],
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_role_history(
    tenant_id: int, employee_id: int, _: RateLimitedUser, request: Request
) -> list[EmployeeRoleOut]:
    return WorkforceService.list_role_history(tenant_id, employee_id)
