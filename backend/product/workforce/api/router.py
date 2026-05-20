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
    """
    Creates a new department under the tenant with the given name/code/colour.
    Returns DepartmentOut with HTTP 201 carrying the persisted department.
    On error returns 409 (name/code collision), 422 (invalid fields), or 429 (rate limit).
    Department code is unique per tenant; name collisions also raise 409.
    """
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
    """
    Lists every department in the tenant (active and deactivated alike).
    Returns list[DepartmentOut] ordered by name ascending.
    On error returns 429 (rate limit); tenant scope is enforced via the URL path.
    Frontends typically filter deactivated rows client-side; no server-side filter is applied here.
    """
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
    """
    Fetches a single department by id, scoped to the tenant.
    Returns DepartmentOut with name, code, colour, and active flag.
    On error returns 404 (department missing in tenant) or 429 (rate limit).
    Cross-tenant lookups are rejected even when the id is valid elsewhere.
    """
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
    """
    Soft-deletes the department by flipping its active flag to false.
    Returns DepartmentOut showing the now-deactivated department.
    On error returns 404 (department missing) or 429 (rate limit).
    Existing employee/department assignments are preserved for history; only new ones are blocked.
    """
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
    """
    Updates editable fields (name/code/colour/active) on an existing department.
    Returns DepartmentOut with the post-update department.
    On error returns 403 (caller cannot manage workforce), 404, 409 (collision), or 429.
    Code uniqueness is re-checked on update; collisions raise 409.
    """
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
    """
    Assigns an employee as a manager of the department starting from the payload's effective date.
    Returns DepartmentManagerOut with HTTP 201 describing the new assignment.
    On error returns 403, 404 (department/employee missing), 409 (already manager), or 429.
    Multiple managers per department are allowed; the assignment is kept as a historical row.
    """
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
    """
    Lists active manager assignments for the department.
    Returns list[DepartmentManagerOut] with employee details and assignment dates.
    On error returns 404 (department missing) or 429 (rate limit).
    Inactive/ended assignments are excluded; use the assignment row id to remove if needed.
    """
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
    """
    Ends a department-manager assignment on the date provided in the payload.
    Returns DepartmentManagerOut showing the assignment with its end_date set.
    On error returns 403, 404 (assignment missing), or 429 (rate limit).
    Closes the assignment without deletion so reporting lines stay reconstructable.
    """
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
    """
    Creates a new role definition (title + level + cost band) for the tenant.
    Returns RoleOut with HTTP 201 carrying the persisted role.
    On error returns 409 (title collision), 422 (invalid fields), or 429 (rate limit).
    Role titles are unique per tenant; collisions raise 409.
    """
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
    """
    Lists every role defined in the tenant (active and deactivated alike).
    Returns list[RoleOut] ordered by title ascending.
    On error returns 429 (rate limit); membership is enforced via the URL path.
    Deactivated roles are included so historical employee-role rows remain interpretable.
    """
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
    """
    Fetches a single role definition by id, scoped to the tenant.
    Returns RoleOut with title, level, cost band, and active flag.
    On error returns 404 (role missing in tenant) or 429 (rate limit).
    Cross-tenant access is denied even with a valid id.
    """
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
    """
    Soft-deletes the role by flipping its active flag to false.
    Returns RoleOut reflecting the deactivated state.
    On error returns 404 (role missing) or 429 (rate limit).
    Existing employee-role assignments remain valid for historical lookup; new assignments are blocked.
    """
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
    """
    Updates editable fields (title/level/cost band/active) on an existing role.
    Returns RoleOut with the post-update role.
    On error returns 403, 404, 409 (title collision), or 429 (rate limit).
    Past employee-role rows are not retroactively updated — only the role definition changes.
    """
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
    """
    Creates a new employee record with optional initial department/role/manager assignments.
    Returns EmployeeOut with HTTP 201 carrying the persisted employee.
    On error returns 404 (referenced dep/role/manager missing), 409 (duplicate code), 422, or 429.
    The orchestrator wires up the initial assignment rows in the same transaction as the employee row.
    """
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
    """
    Lists every employee in the tenant (active and deactivated alike).
    Returns list[EmployeeOut] ordered by full_name ascending.
    On error returns 429 (rate limit); tenant scope is enforced via the URL path.
    Deactivated employees are kept in the list so historical references resolve.
    """
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
    """
    Fetches a single employee by id, scoped to the tenant.
    Returns EmployeeOut with personal details and current department/role/manager pointers.
    On error returns 404 (employee missing in tenant) or 429 (rate limit).
    Cross-tenant access is denied; non-membership surfaces as 404 to avoid leakage.
    """
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
    """
    Soft-deletes the employee by setting active=false and closing open assignments.
    Returns EmployeeOut showing the now-deactivated employee.
    On error returns 404 (employee missing) or 429 (rate limit).
    Linked user account remains intact; only the employee row is deactivated.
    """
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
    """
    Updates editable employee fields (name, code, contact, status) without touching assignments.
    Returns EmployeeOut with the post-update employee.
    On error returns 403, 404, 409 (code collision), 422 (invalid fields), or 429.
    Department/role/manager changes go through their dedicated endpoints, not this one.
    """
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
    """
    Links (or unlinks) an AuthUser account to the employee so that user can act as them in-app.
    Returns EmployeeOut reflecting the updated user_id pointer (null when unlinking).
    On error returns 403, 404 (employee/user missing), 409 (user already linked elsewhere), or 429.
    The linked user must already be a member of the tenant.
    """
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
    """
    Sets (or clears) the manager_id of the employee — used to redraw the reporting line.
    Returns EmployeeOut with the updated manager pointer.
    On error returns 403, 404 (employee or manager missing/in another tenant), or 429.
    Self-referencing managers and cross-tenant managers are rejected by the orchestrator.
    """
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
    """
    Lists employees whose manager_id matches the given employee (their direct reports).
    Returns list[EmployeeOut]; the array is empty if the employee manages no one.
    On error returns 404 (employee missing) or 429 (rate limit).
    Only direct reports are returned — descend recursively in the caller for full org-tree views.
    """
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
    """
    Assigns the employee to a department from the payload's effective_from date.
    Returns EmployeeDepartmentOut with HTTP 201 describing the new assignment row.
    On error returns 404 (employee/department missing) or 429 (rate limit).
    Closes the previously active assignment automatically — there is always at most one active.
    """
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
    """
    Returns the employee's currently active department assignment (the one without an end_date).
    Returns EmployeeDepartmentOut with the active assignment row.
    On error returns 404 (employee missing OR no active department) or 429 (rate limit).
    There is at most one active assignment; older ones are accessible via the history endpoint.
    """
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
    """
    Lists the employee's full history of department assignments (past + current).
    Returns list[EmployeeDepartmentOut] ordered by effective_from descending.
    On error returns 404 (employee missing) or 429 (rate limit).
    Includes closed assignments with their end_date set; the head row is the active one.
    """
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
    """
    Assigns a role to the employee starting from the payload's effective_from date.
    Returns EmployeeRoleOut with HTTP 201 carrying the new assignment.
    On error returns 404 (employee/role missing), 422 (invalid date), or 429.
    Closes the previously active role assignment automatically; only one active role per employee.
    """
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
    """
    Returns the employee's currently active role assignment (the one without an end_date).
    Returns EmployeeRoleOut with the active assignment row.
    On error returns 404 (employee missing OR no active role) or 429 (rate limit).
    At most one role is active at a time; the history endpoint exposes the rest.
    """
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
    """
    Lists the employee's full history of role assignments (past + current).
    Returns list[EmployeeRoleOut] ordered by effective_from descending.
    On error returns 404 (employee missing) or 429 (rate limit).
    Closed assignments retain their end_date; the head row is the currently active role.
    """
    return WorkforceService.list_role_history(tenant_id, employee_id)
