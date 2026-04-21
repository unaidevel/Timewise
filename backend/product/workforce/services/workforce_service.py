from django.db import transaction

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
from product.workforce.entities.workforce_entities import (
    DepartmentEntity,
    EmployeeEntity,
    EmployeeRoleEntity,
    RoleEntity,
)
from product.workforce.exceptions import (
    DepartmentAlreadyExistsError,
    DepartmentNotFoundError,
    EmployeeAlreadyExistsError,
    EmployeeNotFoundError,
    RoleAlreadyExistsError,
    RoleNotFoundError,
)
from product.workforce.repositories.workforce_repository import WorkforceRepository



class WorkforceService:
    @staticmethod
    def _create_default_roles(tenant_id: int) -> None:
        WorkforceRepository._create_default_roles(tenant_id)

    # --- Departments ---

    @staticmethod
    def create_department(tenant_id: int, payload: DepartmentIn) -> DepartmentOut:
        entity = DepartmentEntity(name=payload.name)

        existing_department = WorkforceRepository.find_department_by_name(
            tenant_id, entity.name
        )
        if existing_department:
            raise DepartmentAlreadyExistsError(
                f"A department named '{existing_department.name}' already exists in this tenant."
            )

        return WorkforceRepository.create_department(entity, tenant_id)

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
    def deactivate_department(tenant_id: int, department_id: int) -> DepartmentOut:
        dept = WorkforceRepository.get_department_by_id(department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise DepartmentNotFoundError(f"Department {department_id} not found.")
        result = WorkforceRepository.deactivate_department(department_id)
        if not result:
            raise DepartmentNotFoundError(
                f"Department {department_id} is already inactive."
            )
        return result

    # --- Roles ---

    @staticmethod
    def create_role(tenant_id: int, payload: RoleIn) -> RoleOut:
        entity = RoleEntity(name=payload.name)

        existing_role = WorkforceRepository.find_role_by_name(tenant_id, entity.name)
        if existing_role:
            raise RoleAlreadyExistsError(
                f"A role named '{existing_role.name}' already exists in this tenant."
            )

        return WorkforceRepository.create_role(entity, tenant_id)

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
    def deactivate_role(tenant_id: int, role_id: int) -> RoleOut:
        role = WorkforceRepository.get_role_by_id(role_id)
        if not role or role.tenant_id != tenant_id:
            raise RoleNotFoundError(f"Role {role_id} not found.")
        result = WorkforceRepository.deactivate_role(role_id)
        if not result:
            raise RoleNotFoundError(f"Role {role_id} is already inactive.")
        return result

    # --- Employees ---

    @staticmethod
    def create_employee(tenant_id: int, payload: EmployeeIn) -> EmployeeOut:
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
            )
            WorkforceRepository.assign_department(employee.id, payload.department_id)
            WorkforceRepository.assign_role(employee.id, payload.role_id, role_entity)

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
    def deactivate_employee(tenant_id: int, employee_id: int) -> EmployeeOut:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")
        result = WorkforceRepository.deactivate_employee(employee_id)
        if not result:
            raise EmployeeNotFoundError(f"Employee {employee_id} is already inactive.")
        return result

    # --- Department assignments ---

    @staticmethod
    def assign_department(
        tenant_id: int,
        employee_id: int,
        payload: AssignDepartmentRequest,
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
            WorkforceRepository.close_active_department(employee_id, payload.reason)
            return WorkforceRepository.assign_department(
                employee_id, payload.department_id
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
            WorkforceRepository.close_active_role(employee_id, payload.reason)
            return WorkforceRepository.assign_role(
                employee_id, payload.role_id, role_entity
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
