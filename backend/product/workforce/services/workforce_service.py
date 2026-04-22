from django.db import transaction

from infra.tenants.decorators import only_admin
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
from product.workforce.entities.workforce_entities import (
    DepartmentEntity,
    EmployeeEntity,
    EmployeeRoleEntity,
    EmployeeUpdateEntity,
    RoleEntity,
)
from product.workforce.exceptions import (
    DepartmentAlreadyExistsError,
    DepartmentNotFoundError,
    EmployeeAlreadyExistsError,
    EmployeeNotFoundError,
    ManagerAlreadyAssignedError,
    ManagerAssignmentNotFoundError,
    RoleAlreadyExistsError,
    RoleNotFoundError,
)
from product.workforce.repositories.workforce_repository import WorkforceRepository


class WorkforceService:
    @staticmethod
    def create_default_roles(tenant_id: int) -> None:
        WorkforceRepository._create_default_roles(tenant_id)

    # --- Departments ---

    @staticmethod
    def create_department(
        tenant_id: int,
        payload: DepartmentIn,
        user_id: int | None = None,
    ) -> DepartmentOut:
        entity = DepartmentEntity(name=payload.name)

        existing_department = WorkforceRepository.find_department_by_name(
            tenant_id, entity.name
        )
        if existing_department:
            raise DepartmentAlreadyExistsError(
                f"A department named '{existing_department.name}' already exists in this tenant."
            )

        return WorkforceRepository.create_department(entity, tenant_id, created_by_id=user_id)

    @staticmethod
    def get_department(tenant_id: int, department_id: int) -> DepartmentOut:
        dept = WorkforceRepository.get_department_by_id(department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise DepartmentNotFoundError(f"Department {department_id} not found.")
        return dept

    @staticmethod
    def list_departments(tenant_id: int) -> list[DepartmentOut]:
        return WorkforceRepository.list_departments(tenant_id)

    @staticmethod
    def deactivate_department(
        tenant_id: int,
        department_id: int,
        user_id: int | None = None,
    ) -> DepartmentOut:
        dept = WorkforceRepository.get_department_by_id(department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise DepartmentNotFoundError(f"Department {department_id} not found.")
        result = WorkforceRepository.deactivate_department(department_id, updated_by_id=user_id)
        if not result:
            raise DepartmentNotFoundError(
                f"Department {department_id} is already inactive."
            )
        return result

    @only_admin
    @staticmethod
    def update_department(
        tenant_id: int, department_id: int, payload: DepartmentUpdate, user_id: int
    ) -> DepartmentOut:
        dept = WorkforceRepository.get_department_by_id(department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise DepartmentNotFoundError(f"Department {department_id} not found.")
        entity = DepartmentEntity(name=payload.name)
        existing = WorkforceRepository.find_department_by_name(tenant_id, entity.name)
        if existing and existing.id != department_id:
            raise DepartmentAlreadyExistsError(
                f"A department named '{entity.name}' already exists in this tenant."
            )
        return WorkforceRepository.update_department(department_id, entity.name, updated_by_id=user_id)

    @only_admin
    @staticmethod
    def assign_department_manager(
        tenant_id: int,
        department_id: int,
        payload: AssignDepartmentManagerRequest,
        user_id: int,
    ) -> DepartmentManagerOut:
        dept = WorkforceRepository.get_department_by_id(department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise DepartmentNotFoundError(f"Department {department_id} not found.")
        employee = WorkforceRepository.get_employee_by_id(payload.employee_id)
        if not employee or employee.tenant_id != tenant_id:
            raise EmployeeNotFoundError(f"Employee {payload.employee_id} not found.")
        existing = WorkforceRepository.find_active_department_manager(
            department_id, payload.employee_id
        )
        if existing:
            raise ManagerAlreadyAssignedError(
                f"Employee {payload.employee_id} is already an active manager of department {department_id}."
            )
        return WorkforceRepository.assign_department_manager(
            department_id, payload.employee_id, created_by_id=user_id
        )

    @staticmethod
    def list_department_managers(
        tenant_id: int, department_id: int
    ) -> list[DepartmentManagerOut]:
        dept = WorkforceRepository.get_department_by_id(department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise DepartmentNotFoundError(f"Department {department_id} not found.")
        return WorkforceRepository.get_active_department_managers(department_id)

    @only_admin
    @staticmethod
    def remove_department_manager(
        tenant_id: int,
        department_id: int,
        assignment_id: int,
        payload: RemoveDepartmentManagerRequest,
        user_id: int,
    ) -> DepartmentManagerOut:
        dept = WorkforceRepository.get_department_by_id(department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise DepartmentNotFoundError(f"Department {department_id} not found.")
        result = WorkforceRepository.remove_department_manager(
            assignment_id, payload.reason, updated_by_id=user_id
        )
        if not result:
            raise ManagerAssignmentNotFoundError(
                f"Manager assignment {assignment_id} not found or already removed."
            )
        return result

    # --- Roles ---

    @staticmethod
    def create_role(
        tenant_id: int,
        payload: RoleIn,
        user_id: int | None = None,
    ) -> RoleOut:
        entity = RoleEntity(name=payload.name)

        existing_role = WorkforceRepository.find_role_by_name(tenant_id, entity.name)
        if existing_role:
            raise RoleAlreadyExistsError(
                f"A role named '{existing_role.name}' already exists in this tenant."
            )

        return WorkforceRepository.create_role(entity, tenant_id, created_by_id=user_id)

    @staticmethod
    def get_role(tenant_id: int, role_id: int) -> RoleOut:
        role = WorkforceRepository.get_role_by_id(role_id)
        if not role or role.tenant_id != tenant_id:
            raise RoleNotFoundError(f"Role {role_id} not found.")
        return role

    @staticmethod
    def list_roles(tenant_id: int) -> list[RoleOut]:
        return WorkforceRepository.list_roles(tenant_id)

    @staticmethod
    def deactivate_role(
        tenant_id: int,
        role_id: int,
        user_id: int | None = None,
    ) -> RoleOut:
        role = WorkforceRepository.get_role_by_id(role_id)
        if not role or role.tenant_id != tenant_id:
            raise RoleNotFoundError(f"Role {role_id} not found.")
        result = WorkforceRepository.deactivate_role(role_id, updated_by_id=user_id)
        if not result:
            raise RoleNotFoundError(f"Role {role_id} is already inactive.")
        return result

    @only_admin
    @staticmethod
    def update_role(
        tenant_id: int, role_id: int, payload: RoleUpdate, user_id: int
    ) -> RoleOut:
        role = WorkforceRepository.get_role_by_id(role_id)
        if not role or role.tenant_id != tenant_id:
            raise RoleNotFoundError(f"Role {role_id} not found.")
        entity = RoleEntity(name=payload.name)
        existing = WorkforceRepository.find_role_by_name(tenant_id, entity.name)
        if existing and existing.id != role_id:
            raise RoleAlreadyExistsError(
                f"A role named '{entity.name}' already exists in this tenant."
            )
        return WorkforceRepository.update_role(role_id, entity.name, updated_by_id=user_id)

    # --- Employees ---

    @staticmethod
    def create_employee(
        tenant_id: int,
        payload: EmployeeIn,
        user_id: int | None = None,
    ) -> EmployeeOut:
        entity = EmployeeEntity(
            full_name=payload.full_name,
            email=payload.email,
            hired_at=payload.hired_at,
        )
        role_entity = EmployeeRoleEntity(
            hourly_rate=payload.hourly_rate,
            contract_hours_per_week=payload.contract_hours_per_week,
        )

        dept = WorkforceRepository.get_department_by_id(payload.department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise DepartmentNotFoundError(
                f"Department {payload.department_id} not found."
            )

        role = WorkforceRepository.get_role_by_id(payload.role_id)
        if not role or role.tenant_id != tenant_id:
            raise RoleNotFoundError(f"Role {payload.role_id} not found.")

        existing = WorkforceRepository.find_employee_by_email(tenant_id, entity.email)
        if existing:
            raise EmployeeAlreadyExistsError(
                f"An employee with email '{entity.email}' already exists in this tenant."
            )

        with transaction.atomic():
            employee = WorkforceRepository.create_employee(
                entity=entity,
                tenant_id=tenant_id,
                user_id=payload.user_id,
                created_by_id=user_id,
            )
            WorkforceRepository.assign_department(
                employee.id, payload.department_id, created_by_id=user_id
            )
            WorkforceRepository.assign_role(
                employee.id, payload.role_id, role_entity, created_by_id=user_id
            )

        return employee

    @staticmethod
    def get_employee(tenant_id: int, employee_id: int) -> EmployeeOut:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")
        return emp

    @staticmethod
    def list_employees(tenant_id: int) -> list[EmployeeOut]:
        return WorkforceRepository.list_employees(tenant_id)

    @staticmethod
    def deactivate_employee(
        tenant_id: int,
        employee_id: int,
        user_id: int | None = None,
    ) -> EmployeeOut:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")
        with transaction.atomic():
            WorkforceRepository.close_active_department(
                employee_id, "Employee deactivated", updated_by_id=user_id
            )
            WorkforceRepository.close_active_role(
                employee_id, "Employee deactivated", updated_by_id=user_id
            )
            result = WorkforceRepository.deactivate_employee(employee_id, updated_by_id=user_id)
        if not result:
            raise EmployeeNotFoundError(f"Employee {employee_id} is already inactive.")
        return result

    @only_admin
    @staticmethod
    def update_employee(
        tenant_id: int, employee_id: int, payload: EmployeeUpdate, user_id: int
    ) -> EmployeeOut:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")
        entity = EmployeeUpdateEntity(
            full_name=payload.full_name,
            email=payload.email,
            hired_at=payload.hired_at,
        )
        if entity.email is not None:
            existing = WorkforceRepository.find_employee_by_email(
                tenant_id, entity.email
            )
            if existing and existing.id != employee_id:
                raise EmployeeAlreadyExistsError(
                    f"An employee with email '{entity.email}' already exists in this tenant."
                )
        return WorkforceRepository.update_employee(employee_id, entity, updated_by_id=user_id)

    @only_admin
    @staticmethod
    def set_employee_manager(
        tenant_id: int,
        employee_id: int,
        payload: SetEmployeeManagerRequest,
        user_id: int,
    ) -> EmployeeOut:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")
        if payload.manager_id is not None:
            manager = WorkforceRepository.get_employee_by_id(payload.manager_id)
            if not manager or manager.tenant_id != tenant_id:
                raise EmployeeNotFoundError(f"Employee {payload.manager_id} not found.")
        return WorkforceRepository.set_employee_manager(
            employee_id, payload.manager_id, updated_by_id=user_id
        )

    @staticmethod
    def get_direct_reports(tenant_id: int, employee_id: int) -> list[EmployeeOut]:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")
        return WorkforceRepository.get_direct_reports(employee_id)

    # --- Department assignments ---

    @staticmethod
    def assign_department(
        tenant_id: int,
        employee_id: int,
        payload: AssignDepartmentRequest,
        user_id: int | None = None,
    ) -> EmployeeDepartmentOut:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")

        dept = WorkforceRepository.get_department_by_id(payload.department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise DepartmentNotFoundError(
                f"Department {payload.department_id} not found."
            )

        with transaction.atomic():
            WorkforceRepository.close_active_department(
                employee_id, payload.reason, updated_by_id=user_id
            )
            return WorkforceRepository.assign_department(
                employee_id, payload.department_id, created_by_id=user_id
            )

    @staticmethod
    def get_active_department(
        tenant_id: int, employee_id: int
    ) -> EmployeeDepartmentOut:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")
        assignment = WorkforceRepository.get_active_department(employee_id)
        if not assignment:
            raise DepartmentNotFoundError(
                f"Employee {employee_id} has no active department assignment."
            )
        return assignment

    @staticmethod
    def list_department_history(
        tenant_id: int, employee_id: int
    ) -> list[EmployeeDepartmentOut]:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")
        return WorkforceRepository.list_department_assignments(employee_id)

    # --- Role assignments ---

    @staticmethod
    def assign_role(
        tenant_id: int,
        employee_id: int,
        payload: AssignRoleRequest,
        user_id: int | None = None,
    ) -> EmployeeRoleOut:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")

        role = WorkforceRepository.get_role_by_id(payload.role_id)
        if not role or role.tenant_id != tenant_id:
            raise RoleNotFoundError(f"Role {payload.role_id} not found.")

        role_entity = EmployeeRoleEntity(
            hourly_rate=payload.hourly_rate,
            contract_hours_per_week=payload.contract_hours_per_week,
        )

        with transaction.atomic():
            WorkforceRepository.close_active_role(
                employee_id, payload.reason, updated_by_id=user_id
            )
            return WorkforceRepository.assign_role(
                employee_id, payload.role_id, role_entity, created_by_id=user_id
            )

    @staticmethod
    def get_active_role(tenant_id: int, employee_id: int) -> EmployeeRoleOut:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")
        assignment = WorkforceRepository.get_active_role(employee_id)
        if not assignment:
            raise RoleNotFoundError(
                f"Employee {employee_id} has no active role assignment."
            )
        return assignment

    @staticmethod
    def list_role_history(tenant_id: int, employee_id: int) -> list[EmployeeRoleOut]:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")
        return WorkforceRepository.list_role_assignments(employee_id)
