from typing import Literal

from django.db import transaction
from django.utils import timezone

from infra.common.classes import MembershipRoles
from infra.common.exceptions import Conflict, Forbidden, NotFound
from infra.tenants.decorators import only_admin
from infra.tenants.repositories.tenants_repository import TenantRepository
from product.common.classes import WorkforceRoles
from product.workforce.dtos.dtos import (
    DepartmentManagerOut,
    DepartmentOut,
    EmployeeDepartmentOut,
    EmployeeOut,
    EmployeeRoleOut,
    RoleOut,
)
from product.workforce.entities.workforce_entities import (
    AssignDepartmentEntity,
    AssignDepartmentManagerEntity,
    AssignRoleEntity,
    CreateEmployeeEntity,
    DepartmentEntity,
    DepartmentUpdateEntity,
    EmployeeEntity,
    EmployeeRoleEntity,
    EmployeeUpdateEntity,
    LinkEmployeeUserEntity,
    RemoveDepartmentManagerEntity,
    RoleEntity,
    RoleUpdateEntity,
    SetEmployeeManagerEntity,
)
from product.workforce.repositories.workforce_repository import WorkforceRepository

Scope = Literal["mine", "all"]

ELEVATED_MEMBERSHIP_ROLES = frozenset(
    {MembershipRoles.OWNER.value, MembershipRoles.ADMIN.value}
)


class WorkforceService:
    _DEFAULT_ROLES: list[tuple[str, str]] = [
        ("Manager", WorkforceRoles.MANAGER.value),
        ("Employee", WorkforceRoles.EMPLOYEE.value),
        ("Intern", WorkforceRoles.INTERN.value),
        ("Freelance", WorkforceRoles.FREELANCE.value),
    ]

    @staticmethod
    def create_default_roles(tenant_id: int) -> None:
        WorkforceRepository.bulk_create_roles(
            tenant_id, WorkforceService._DEFAULT_ROLES
        )

    @staticmethod
    def get_visible_employee_ids(
        tenant_id: int, user_id: int, scope: Scope = "mine"
    ) -> set[int] | None:
        """
        Returns the set of employee_ids the caller may see, or None meaning
        "no restriction" (owner/admin with scope='all').

        Raises Forbidden if the caller is not a tenant member, or if a
        non-elevated caller requests scope='all'.
        """
        membership = TenantRepository.find_active_membership(tenant_id, user_id)
        if not membership:
            raise Forbidden("Not a member of this tenant.")

        is_elevated = membership.role in ELEVATED_MEMBERSHIP_ROLES
        own = WorkforceRepository.find_employee_by_user_id(tenant_id, user_id)

        if is_elevated:
            if scope == "all":
                return None
            return {own.id} if own else set()

        if scope == "all":
            raise Forbidden("You may only view your own records.")

        if not own:
            return set()

        role_type = WorkforceRepository.get_active_role_type_for_employee(own.id)
        if role_type == WorkforceRoles.MANAGER.value:
            reports = WorkforceRepository.get_direct_reports(own.id)
            return {own.id, *(r.id for r in reports)}

        return {own.id}

    @staticmethod
    def ensure_can_access_employee(
        tenant_id: int, user_id: int, employee_id: int
    ) -> None:
        """
        Raises Forbidden if the caller cannot act on resources owned by
        the given employee.

        Owner/admin (tenant membership) always pass. Workforce managers
        pass for self and direct reports. Everyone else passes only for
        themselves.
        """
        membership = TenantRepository.find_active_membership(tenant_id, user_id)
        if not membership:
            raise Forbidden("Not a member of this tenant.")

        if membership.role in ELEVATED_MEMBERSHIP_ROLES:
            return

        own = WorkforceRepository.find_employee_by_user_id(tenant_id, user_id)
        if not own:
            raise Forbidden("No employee profile for this user in tenant.")
        if own.id == employee_id:
            return

        role_type = WorkforceRepository.get_active_role_type_for_employee(own.id)
        if role_type == WorkforceRoles.MANAGER.value:
            reports = WorkforceRepository.get_direct_reports(own.id)
            if any(r.id == employee_id for r in reports):
                return

        raise Forbidden("You may not access this resource.")

    @staticmethod
    def create_department(
        tenant_id: int,
        entity: DepartmentEntity,
        user_id: int | None = None,
    ) -> DepartmentOut:
        existing_department = WorkforceRepository.find_department_by_name(
            tenant_id, entity.name
        )
        if existing_department:
            raise Conflict(
                f"A department named '{existing_department.name}' already exists in this tenant."
            )

        return WorkforceRepository.create_department(entity, tenant_id, user_id)

    @staticmethod
    def get_department(tenant_id: int, department_id: int) -> DepartmentOut:
        dept = WorkforceRepository.get_department_by_id(department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise NotFound(f"Department {department_id} not found.")
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
            raise NotFound(f"Department {department_id} not found.")
        result = WorkforceRepository.deactivate_department(department_id, user_id)
        if not result:
            raise NotFound(f"Department {department_id} is already inactive.")
        return result

    @only_admin
    @staticmethod
    def update_department(
        tenant_id: int, entity: DepartmentUpdateEntity, user_id: int
    ) -> DepartmentOut:
        dept = WorkforceRepository.get_department_by_id(entity.department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise NotFound(f"Department {entity.department_id} not found.")
        existing = WorkforceRepository.find_department_by_name(tenant_id, entity.name)
        if existing and existing.id != entity.department_id:
            raise Conflict(
                f"A department named '{entity.name}' already exists in this tenant."
            )
        return WorkforceRepository.update_department(entity, user_id)

    @only_admin
    @staticmethod
    def assign_department_manager(
        tenant_id: int,
        department_id: int,
        entity: AssignDepartmentManagerEntity,
        user_id: int,
    ) -> DepartmentManagerOut:
        dept = WorkforceRepository.get_department_by_id(department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise NotFound(f"Department {department_id} not found.")
        employee = WorkforceRepository.get_employee_by_id(entity.employee_id)
        if not employee or employee.tenant_id != tenant_id:
            raise NotFound(f"Employee {entity.employee_id} not found.")
        existing = WorkforceRepository.find_active_department_manager(
            department_id, entity.employee_id
        )
        if existing:
            raise Conflict(
                f"Employee {entity.employee_id} is already an active manager of department {department_id}."
            )
        return WorkforceRepository.assign_department_manager(
            department_id, entity.employee_id, user_id
        )

    @staticmethod
    def list_department_managers(
        tenant_id: int, department_id: int
    ) -> list[DepartmentManagerOut]:
        dept = WorkforceRepository.get_department_by_id(department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise NotFound(f"Department {department_id} not found.")
        return WorkforceRepository.get_active_department_managers(department_id)

    @only_admin
    @staticmethod
    def remove_department_manager(
        tenant_id: int,
        department_id: int,
        assignment_id: int,
        entity: RemoveDepartmentManagerEntity,
        user_id: int,
    ) -> DepartmentManagerOut:
        dept = WorkforceRepository.get_department_by_id(department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise NotFound(f"Department {department_id} not found.")
        result = WorkforceRepository.remove_department_manager(
            assignment_id, entity.reason, timezone.now(), user_id
        )
        if not result:
            raise NotFound(
                f"Manager assignment {assignment_id} not found or already removed."
            )
        return result

    @staticmethod
    def create_role(
        tenant_id: int,
        entity: RoleEntity,
        user_id: int | None = None,
    ) -> RoleOut:
        existing_role = WorkforceRepository.find_role_by_name(tenant_id, entity.name)
        if existing_role:
            raise Conflict(
                f"A role named '{existing_role.name}' already exists in this tenant."
            )

        return WorkforceRepository.create_role(entity, tenant_id, user_id)

    @staticmethod
    def get_role(tenant_id: int, role_id: int) -> RoleOut:
        role = WorkforceRepository.get_role_by_id(role_id)
        if not role or role.tenant_id != tenant_id:
            raise NotFound(f"Role {role_id} not found.")
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
            raise NotFound(f"Role {role_id} not found.")
        result = WorkforceRepository.deactivate_role(role_id, user_id)
        if not result:
            raise NotFound(f"Role {role_id} is already inactive.")
        return result

    @only_admin
    @staticmethod
    def update_role(tenant_id: int, entity: RoleUpdateEntity, user_id: int) -> RoleOut:
        role = WorkforceRepository.get_role_by_id(entity.role_id)
        if not role or role.tenant_id != tenant_id:
            raise NotFound(f"Role {entity.role_id} not found.")
        existing = WorkforceRepository.find_role_by_name(tenant_id, entity.name)
        if existing and existing.id != entity.role_id:
            raise Conflict(
                f"A role named '{entity.name}' already exists in this tenant."
            )
        return WorkforceRepository.update_role(entity, user_id)

    @staticmethod
    def create_employee(
        tenant_id: int,
        entity: CreateEmployeeEntity,
        user_id: int | None = None,
    ) -> EmployeeOut:
        employee_entity = EmployeeEntity(
            full_name=entity.full_name,
            email=entity.email,
            hired_at=entity.hired_at,
        )
        role_entity = EmployeeRoleEntity(
            hourly_rate=entity.hourly_rate,
            contract_hours_per_week=entity.contract_hours_per_week,
        )

        dept = WorkforceRepository.get_department_by_id(entity.department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise NotFound(f"Department {entity.department_id} not found.")

        role = WorkforceRepository.get_role_by_id(entity.role_id)
        if not role or role.tenant_id != tenant_id:
            raise NotFound(f"Role {entity.role_id} not found.")

        existing = WorkforceRepository.find_employee_by_email(
            tenant_id, employee_entity.email
        )
        if existing:
            raise Conflict(
                f"An employee with email '{employee_entity.email}' already exists in this tenant."
            )

        if entity.manager_id is not None:
            manager = WorkforceRepository.get_employee_by_id(entity.manager_id)
            if not manager or manager.tenant_id != tenant_id:
                raise NotFound(f"Manager employee {entity.manager_id} not found.")

        with transaction.atomic():
            employee = WorkforceRepository.create_employee(
                employee_entity,
                tenant_id,
                entity.user_id,
                user_id,
            )
            WorkforceRepository.assign_department(
                employee.id, entity.department_id, user_id
            )
            WorkforceRepository.assign_role(
                employee.id, entity.role_id, role_entity, user_id
            )
            if entity.manager_id is not None:
                WorkforceRepository.set_employee_manager(
                    SetEmployeeManagerEntity(
                        employee_id=employee.id, manager_id=entity.manager_id
                    ),
                    user_id,
                )
            if entity.is_department_manager:
                WorkforceRepository.assign_department_manager(
                    entity.department_id, employee.id, user_id
                )

        return employee

    @staticmethod
    def get_employee(tenant_id: int, employee_id: int) -> EmployeeOut:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise NotFound(f"Employee {employee_id} not found.")
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
            raise NotFound(f"Employee {employee_id} not found.")
        with transaction.atomic():
            WorkforceRepository.close_active_department(
                employee_id, "Employee deactivated", timezone.now(), user_id
            )
            WorkforceRepository.close_active_role(
                employee_id, "Employee deactivated", timezone.now(), user_id
            )
            result = WorkforceRepository.deactivate_employee(employee_id, user_id)
        if not result:
            raise NotFound(f"Employee {employee_id} is already inactive.")
        return result

    @only_admin
    @staticmethod
    def update_employee(
        tenant_id: int, entity: EmployeeUpdateEntity, user_id: int
    ) -> EmployeeOut:
        emp = WorkforceRepository.get_employee_by_id(entity.employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise NotFound(f"Employee {entity.employee_id} not found.")
        existing = WorkforceRepository.find_employee_by_email(tenant_id, entity.email)
        if existing and existing.id != entity.employee_id:
            raise Conflict(
                f"An employee with email '{entity.email}' already exists in this tenant."
            )
        return WorkforceRepository.update_employee(entity, user_id)

    @only_admin
    @staticmethod
    def link_user(
        tenant_id: int,
        entity: LinkEmployeeUserEntity,
        user_id: int,
    ) -> EmployeeOut:
        emp = WorkforceRepository.get_employee_by_id(entity.employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise NotFound(f"Employee {entity.employee_id} not found.")
        if emp.user_id is not None:
            raise Conflict(
                f"Employee {entity.employee_id} is already linked to a user."
            )
        existing = WorkforceRepository.find_employee_by_user_id(
            tenant_id, entity.user_id
        )
        if existing:
            raise Conflict(
                f"User {entity.user_id} is already linked to employee {existing.id} in this tenant."
            )
        return WorkforceRepository.link_user(entity, user_id)

    @only_admin
    @staticmethod
    def set_employee_manager(
        tenant_id: int,
        entity: SetEmployeeManagerEntity,
        user_id: int,
    ) -> EmployeeOut:
        emp = WorkforceRepository.get_employee_by_id(entity.employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise NotFound(f"Employee {entity.employee_id} not found.")
        if entity.manager_id is not None:
            manager = WorkforceRepository.get_employee_by_id(entity.manager_id)
            if not manager or manager.tenant_id != tenant_id:
                raise NotFound(f"Employee {entity.manager_id} not found.")
        return WorkforceRepository.set_employee_manager(entity, user_id)

    @staticmethod
    def get_direct_reports(tenant_id: int, employee_id: int) -> list[EmployeeOut]:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise NotFound(f"Employee {employee_id} not found.")
        return WorkforceRepository.get_direct_reports(employee_id)

    @staticmethod
    def assign_department(
        tenant_id: int,
        employee_id: int,
        entity: AssignDepartmentEntity,
        user_id: int | None = None,
    ) -> EmployeeDepartmentOut:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise NotFound(f"Employee {employee_id} not found.")

        dept = WorkforceRepository.get_department_by_id(entity.department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise NotFound(f"Department {entity.department_id} not found.")

        with transaction.atomic():
            WorkforceRepository.close_active_department(
                employee_id,
                entity.reason,
                timezone.now(),
                user_id,
            )
            return WorkforceRepository.assign_department(
                employee_id, entity.department_id, user_id
            )

    @staticmethod
    def get_active_department(
        tenant_id: int, employee_id: int
    ) -> EmployeeDepartmentOut:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise NotFound(f"Employee {employee_id} not found.")
        assignment = WorkforceRepository.get_active_department(employee_id)
        if not assignment:
            raise NotFound(
                f"Employee {employee_id} has no active department assignment."
            )
        return assignment

    @staticmethod
    def list_department_history(
        tenant_id: int, employee_id: int
    ) -> list[EmployeeDepartmentOut]:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise NotFound(f"Employee {employee_id} not found.")
        return WorkforceRepository.list_department_assignments(employee_id)

    @staticmethod
    def assign_role(
        tenant_id: int,
        employee_id: int,
        entity: AssignRoleEntity,
        user_id: int | None = None,
    ) -> EmployeeRoleOut:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise NotFound(f"Employee {employee_id} not found.")

        role = WorkforceRepository.get_role_by_id(entity.role_id)
        if not role or role.tenant_id != tenant_id:
            raise NotFound(f"Role {entity.role_id} not found.")

        role_entity = EmployeeRoleEntity(
            hourly_rate=entity.hourly_rate,
            contract_hours_per_week=entity.contract_hours_per_week,
        )

        with transaction.atomic():
            WorkforceRepository.close_active_role(
                employee_id,
                entity.reason,
                timezone.now(),
                user_id,
            )
            return WorkforceRepository.assign_role(
                employee_id, entity.role_id, role_entity, user_id
            )

    @staticmethod
    def get_active_role(tenant_id: int, employee_id: int) -> EmployeeRoleOut:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise NotFound(f"Employee {employee_id} not found.")
        assignment = WorkforceRepository.get_active_role(employee_id)
        if not assignment:
            raise NotFound(f"Employee {employee_id} has no active role assignment.")
        return assignment

    @staticmethod
    def list_role_history(tenant_id: int, employee_id: int) -> list[EmployeeRoleOut]:
        emp = WorkforceRepository.get_employee_by_id(employee_id)
        if not emp or emp.tenant_id != tenant_id:
            raise NotFound(f"Employee {employee_id} not found.")
        return WorkforceRepository.list_role_assignments(employee_id)
