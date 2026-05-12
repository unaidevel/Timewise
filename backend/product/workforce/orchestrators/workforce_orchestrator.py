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
    AssignDepartmentEntity,
    AssignDepartmentManagerEntity,
    AssignRoleEntity,
    CreateEmployeeEntity,
    DepartmentEntity,
    DepartmentUpdateEntity,
    EmployeeUpdateEntity,
    RemoveDepartmentManagerEntity,
    RoleEntity,
    RoleUpdateEntity,
    SetEmployeeManagerEntity,
)
from product.workforce.services.workforce_service import WorkforceService
from shared.audit.dtos.dtos import AuditEventIn
from shared.audit.services.audit_service import AuditService
from shared.audit.utils import AUDITED_FAILURES, AuditOutcome, record_failure


class WorkforceOrchestrator:
    # --- Departments ---

    @only_admin
    @staticmethod
    def create_department(
        tenant_id: int,
        payload: DepartmentIn,
        user_id: int,
    ) -> DepartmentOut:
        entity = DepartmentEntity(name=payload.name)
        try:
            with transaction.atomic():
                dept = WorkforceService.create_department(tenant_id, entity, user_id)
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="department.created",
                        resource_type="Department",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=dept.id,
                        metadata={"name": dept.name},
                    ),
                    user_id,
                )
                return dept
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="department.created",
                resource_type="Department",
                resource_id=None,
                metadata={"name": entity.name},
                exc=exc,
            )
            raise

    @only_admin
    @staticmethod
    def update_department(
        tenant_id: int,
        department_id: int,
        payload: DepartmentUpdate,
        user_id: int,
    ) -> DepartmentOut:
        entity = DepartmentUpdateEntity(department_id=department_id, name=payload.name)
        try:
            with transaction.atomic():
                dept = WorkforceService.update_department(tenant_id, entity, user_id)
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="department.updated",
                        resource_type="Department",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=dept.id,
                        metadata={"name": dept.name},
                    ),
                    user_id,
                )
                return dept
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="department.updated",
                resource_type="Department",
                resource_id=department_id,
                metadata={"name": entity.name},
                exc=exc,
            )
            raise

    @only_admin
    @staticmethod
    def deactivate_department(
        tenant_id: int,
        department_id: int,
        user_id: int,
    ) -> DepartmentOut:
        try:
            with transaction.atomic():
                dept = WorkforceService.deactivate_department(
                    tenant_id, department_id, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="department.deactivated",
                        resource_type="Department",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=dept.id,
                    ),
                    user_id,
                )
                return dept
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="department.deactivated",
                resource_type="Department",
                resource_id=department_id,
                metadata={},
                exc=exc,
            )
            raise

    @only_admin
    @staticmethod
    def assign_department_manager(
        tenant_id: int,
        department_id: int,
        payload: AssignDepartmentManagerRequest,
        user_id: int,
    ) -> DepartmentManagerOut:
        entity = AssignDepartmentManagerEntity(employee_id=payload.employee_id)
        try:
            with transaction.atomic():
                assignment = WorkforceService.assign_department_manager(
                    tenant_id, department_id, entity, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="department_manager.assigned",
                        resource_type="Department",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=department_id,
                        metadata={"employee_id": entity.employee_id},
                    ),
                    user_id,
                )
                return assignment
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="department_manager.assigned",
                resource_type="Department",
                resource_id=department_id,
                metadata={"employee_id": entity.employee_id},
                exc=exc,
            )
            raise

    @only_admin
    @staticmethod
    def remove_department_manager(
        tenant_id: int,
        department_id: int,
        assignment_id: int,
        payload: RemoveDepartmentManagerRequest,
        user_id: int,
    ) -> DepartmentManagerOut:
        entity = RemoveDepartmentManagerEntity(reason=payload.reason)
        try:
            with transaction.atomic():
                assignment = WorkforceService.remove_department_manager(
                    tenant_id, department_id, assignment_id, entity, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="department_manager.removed",
                        resource_type="Department",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=department_id,
                        metadata={"assignment_id": assignment_id},
                    ),
                    user_id,
                )
                return assignment
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="department_manager.removed",
                resource_type="Department",
                resource_id=department_id,
                metadata={"assignment_id": assignment_id},
                exc=exc,
            )
            raise

    # --- Roles ---

    @only_admin
    @staticmethod
    def create_role(
        tenant_id: int,
        payload: RoleIn,
        user_id: int,
    ) -> RoleOut:
        entity = RoleEntity(name=payload.name)
        try:
            with transaction.atomic():
                role = WorkforceService.create_role(tenant_id, entity, user_id)
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="role.created",
                        resource_type="Role",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=role.id,
                        metadata={"name": role.name},
                    ),
                    user_id,
                )
                return role
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="role.created",
                resource_type="Role",
                resource_id=None,
                metadata={"name": entity.name},
                exc=exc,
            )
            raise

    @only_admin
    @staticmethod
    def update_role(
        tenant_id: int,
        role_id: int,
        payload: RoleUpdate,
        user_id: int,
    ) -> RoleOut:
        entity = RoleUpdateEntity(role_id=role_id, name=payload.name)
        try:
            with transaction.atomic():
                role = WorkforceService.update_role(tenant_id, entity, user_id)
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="role.updated",
                        resource_type="Role",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=role.id,
                        metadata={"name": role.name},
                    ),
                    user_id,
                )
                return role
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="role.updated",
                resource_type="Role",
                resource_id=role_id,
                metadata={"name": entity.name},
                exc=exc,
            )
            raise

    @only_admin
    @staticmethod
    def deactivate_role(
        tenant_id: int,
        role_id: int,
        user_id: int,
    ) -> RoleOut:
        try:
            with transaction.atomic():
                role = WorkforceService.deactivate_role(tenant_id, role_id, user_id)
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="role.deactivated",
                        resource_type="Role",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=role.id,
                    ),
                    user_id,
                )
                return role
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="role.deactivated",
                resource_type="Role",
                resource_id=role_id,
                metadata={},
                exc=exc,
            )
            raise

    # --- Employees ---

    @only_admin
    @staticmethod
    def create_employee(
        tenant_id: int,
        payload: EmployeeIn,
        user_id: int,
    ) -> EmployeeOut:
        entity = CreateEmployeeEntity(
            full_name=payload.full_name,
            email=payload.email,
            hired_at=payload.hired_at,
            department_id=payload.department_id,
            role_id=payload.role_id,
            hourly_rate=payload.hourly_rate,
            contract_hours_per_week=payload.contract_hours_per_week,
            user_id=payload.user_id,
        )
        try:
            with transaction.atomic():
                employee = WorkforceService.create_employee(tenant_id, entity, user_id)
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="employee.created",
                        resource_type="Employee",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=employee.id,
                        metadata={
                            "email": employee.email,
                            "department_id": entity.department_id,
                            "role_id": entity.role_id,
                        },
                    ),
                    user_id,
                )
                return employee
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="employee.created",
                resource_type="Employee",
                resource_id=None,
                metadata={"email": entity.email},
                exc=exc,
            )
            raise

    @only_admin
    @staticmethod
    def update_employee(
        tenant_id: int,
        employee_id: int,
        payload: EmployeeUpdate,
        user_id: int,
    ) -> EmployeeOut:
        entity = EmployeeUpdateEntity(employee_id=employee_id, **payload.model_dump())
        try:
            with transaction.atomic():
                employee = WorkforceService.update_employee(tenant_id, entity, user_id)
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="employee.updated",
                        resource_type="Employee",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=employee.id,
                        metadata={"email": employee.email},
                    ),
                    user_id,
                )
                return employee
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="employee.updated",
                resource_type="Employee",
                resource_id=employee_id,
                metadata={"email": entity.email},
                exc=exc,
            )
            raise

    @only_admin
    @staticmethod
    def deactivate_employee(
        tenant_id: int,
        employee_id: int,
        user_id: int,
    ) -> EmployeeOut:
        try:
            with transaction.atomic():
                employee = WorkforceService.deactivate_employee(
                    tenant_id, employee_id, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="employee.deactivated",
                        resource_type="Employee",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=employee.id,
                    ),
                    user_id,
                )
                return employee
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="employee.deactivated",
                resource_type="Employee",
                resource_id=employee_id,
                metadata={},
                exc=exc,
            )
            raise

    @only_admin
    @staticmethod
    def set_employee_manager(
        tenant_id: int,
        employee_id: int,
        payload: SetEmployeeManagerRequest,
        user_id: int,
    ) -> EmployeeOut:
        entity = SetEmployeeManagerEntity(
            employee_id=employee_id, manager_id=payload.manager_id
        )
        try:
            with transaction.atomic():
                employee = WorkforceService.set_employee_manager(
                    tenant_id, entity, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="employee.manager_set",
                        resource_type="Employee",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=employee.id,
                        metadata={"manager_id": entity.manager_id},
                    ),
                    user_id,
                )
                return employee
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="employee.manager_set",
                resource_type="Employee",
                resource_id=employee_id,
                metadata={"manager_id": entity.manager_id},
                exc=exc,
            )
            raise

    # --- Department assignments ---

    @only_admin
    @staticmethod
    def assign_department(
        tenant_id: int,
        employee_id: int,
        payload: AssignDepartmentRequest,
        user_id: int,
    ) -> EmployeeDepartmentOut:
        entity = AssignDepartmentEntity(
            department_id=payload.department_id, reason=payload.reason
        )
        try:
            with transaction.atomic():
                assignment = WorkforceService.assign_department(
                    tenant_id, employee_id, entity, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="employee.department_assigned",
                        resource_type="Employee",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=employee_id,
                        metadata={"department_id": entity.department_id},
                    ),
                    user_id,
                )
                return assignment
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="employee.department_assigned",
                resource_type="Employee",
                resource_id=employee_id,
                metadata={"department_id": entity.department_id},
                exc=exc,
            )
            raise

    # --- Role assignments ---

    @only_admin
    @staticmethod
    def assign_role(
        tenant_id: int,
        employee_id: int,
        payload: AssignRoleRequest,
        user_id: int,
    ) -> EmployeeRoleOut:
        entity = AssignRoleEntity(
            role_id=payload.role_id,
            hourly_rate=payload.hourly_rate,
            contract_hours_per_week=payload.contract_hours_per_week,
            reason=payload.reason,
        )
        try:
            with transaction.atomic():
                assignment = WorkforceService.assign_role(
                    tenant_id, employee_id, entity, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="employee.role_assigned",
                        resource_type="Employee",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=employee_id,
                        metadata={
                            "role_id": entity.role_id,
                            "hourly_rate": str(entity.hourly_rate),
                        },
                    ),
                    user_id,
                )
                return assignment
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="employee.role_assigned",
                resource_type="Employee",
                resource_id=employee_id,
                metadata={"role_id": entity.role_id},
                exc=exc,
            )
            raise
