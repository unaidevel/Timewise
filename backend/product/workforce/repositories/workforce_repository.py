from django.utils import timezone

from product.workforce.dtos.dtos import (
    DepartmentOut,
    EmployeeDepartmentOut,
    EmployeeOut,
    EmployeeRoleOut,
    RoleOut,
)
from product.workforce.entities.workforce_entities import (
    DepartmentEntity,
    EmployeeEntity,
    EmployeeRoleEntity,
    RoleEntity,
)
from product.workforce.models import (
    DepartmentModel,
    EmployeeDepartmentModel,
    EmployeeModel,
    EmployeeRoleModel,
    RoleModel,
)


class WorkforceRepository:
    @staticmethod
    def create_department(entity: DepartmentEntity, tenant_id: int) -> DepartmentOut:
        if not isinstance(entity, DepartmentEntity):
            raise TypeError(f"Expected DepartmentEntity, got {type(entity).__name__}")
        model = DepartmentModel.objects.create(tenant_id=tenant_id, name=entity.name)
        return DepartmentOut.model_validate(model)

    @staticmethod
    def get_department_by_id(department_id: int) -> DepartmentOut | None:
        model = DepartmentModel.objects.filter(id=department_id).first()
        return DepartmentOut.model_validate(model) if model else None

    @staticmethod
    def find_department_by_name(tenant_id: int, name: str) -> DepartmentOut | None:
        model = DepartmentModel.objects.filter(
            tenant_id=tenant_id, name__iexact=name
        ).first()
        return DepartmentOut.model_validate(model) if model else None

    @staticmethod
    def list_departments(tenant_id: int) -> list[DepartmentOut]:
        return [
            DepartmentOut.model_validate(m)
            for m in DepartmentModel.objects.filter(tenant_id=tenant_id).order_by(
                "name"
            )
        ]

    @staticmethod
    def deactivate_department(department_id: int) -> DepartmentOut | None:
        rows = DepartmentModel.objects.filter(id=department_id, is_active=True).update(
            is_active=False
        )
        if rows == 0:
            return None
        model = DepartmentModel.objects.get(id=department_id)
        return DepartmentOut.model_validate(model)

    @staticmethod
    def create_role(entity: RoleEntity, tenant_id: int) -> RoleOut:
        if not isinstance(entity, RoleEntity):
            raise TypeError(f"Expected RoleEntity, got {type(entity).__name__}")
        model = RoleModel.objects.create(tenant_id=tenant_id, name=entity.name)
        return RoleOut.model_validate(model)

    @staticmethod
    def get_role_by_id(role_id: int) -> RoleOut | None:
        model = RoleModel.objects.filter(id=role_id).first()
        return RoleOut.model_validate(model) if model else None

    @staticmethod
    def find_role_by_name(tenant_id: int, name: str) -> RoleOut | None:
        model = RoleModel.objects.filter(tenant_id=tenant_id, name__iexact=name).first()
        return RoleOut.model_validate(model) if model else None

    @staticmethod
    def list_roles(tenant_id: int) -> list[RoleOut]:
        return [
            RoleOut.model_validate(m)
            for m in RoleModel.objects.filter(tenant_id=tenant_id).order_by("name")
        ]

    @staticmethod
    def deactivate_role(role_id: int) -> RoleOut | None:
        rows = RoleModel.objects.filter(id=role_id, is_active=True).update(
            is_active=False
        )
        if rows == 0:
            return None
        model = RoleModel.objects.get(id=role_id)
        return RoleOut.model_validate(model)

    @staticmethod
    def create_employee(
        entity: EmployeeEntity,
        tenant_id: int,
        user_id: int | None = None,
    ) -> EmployeeOut:
        if not isinstance(entity, EmployeeEntity):
            raise TypeError(f"Expected EmployeeEntity, got {type(entity).__name__}")
        model = EmployeeModel.objects.create(
            tenant_id=tenant_id,
            user_id=user_id,
            full_name=entity.full_name,
            email=entity.email,
            hired_at=entity.hired_at,
        )
        return EmployeeOut.model_validate(model)

    @staticmethod
    def get_employee_by_id(employee_id: int) -> EmployeeOut | None:
        model = EmployeeModel.objects.filter(id=employee_id).first()
        return EmployeeOut.model_validate(model) if model else None

    @staticmethod
    def find_employee_by_email(tenant_id: int, email: str) -> EmployeeOut | None:
        model = EmployeeModel.objects.filter(tenant_id=tenant_id, email=email).first()
        return EmployeeOut.model_validate(model) if model else None

    @staticmethod
    def list_employees(tenant_id: int) -> list[EmployeeOut]:
        return [
            EmployeeOut.model_validate(m)
            for m in EmployeeModel.objects.filter(tenant_id=tenant_id).order_by(
                "full_name"
            )
        ]

    @staticmethod
    def deactivate_employee(employee_id: int) -> EmployeeOut | None:
        rows = EmployeeModel.objects.filter(id=employee_id, is_active=True).update(
            is_active=False
        )
        if rows == 0:
            return None
        model = EmployeeModel.objects.get(id=employee_id)
        return EmployeeOut.model_validate(model)

    @staticmethod
    def assign_department(
        employee_id: int, department_id: int
    ) -> EmployeeDepartmentOut:
        model = EmployeeDepartmentModel.objects.create(
            employee_id=employee_id,
            department_id=department_id,
        )
        return EmployeeDepartmentOut.model_validate(model)

    @staticmethod
    def get_active_department(employee_id: int) -> EmployeeDepartmentOut | None:
        model = EmployeeDepartmentModel.objects.filter(
            employee_id=employee_id,
            left_at__isnull=True,
        ).first()
        return EmployeeDepartmentOut.model_validate(model) if model else None

    @staticmethod
    def list_department_assignments(employee_id: int) -> list[EmployeeDepartmentOut]:
        return [
            EmployeeDepartmentOut.model_validate(m)
            for m in EmployeeDepartmentModel.objects.filter(
                employee_id=employee_id
            ).order_by("assigned_at")
        ]

    @staticmethod
    def close_active_department(
        employee_id: int, reason: str
    ) -> EmployeeDepartmentOut | None:
        rows = EmployeeDepartmentModel.objects.filter(
            employee_id=employee_id,
            left_at__isnull=True,
        ).update(left_at=timezone.now(), left_reason=reason)
        if rows == 0:
            return None
        model = (
            EmployeeDepartmentModel.objects.filter(employee_id=employee_id)
            .order_by("-assigned_at")
            .first()
        )
        return EmployeeDepartmentOut.model_validate(model)

    @staticmethod
    def assign_role(
        employee_id: int,
        role_id: int,
        entity: EmployeeRoleEntity,
    ) -> EmployeeRoleOut:
        if not isinstance(entity, EmployeeRoleEntity):
            raise TypeError(f"Expected EmployeeRoleEntity, got {type(entity).__name__}")
        model = EmployeeRoleModel.objects.create(
            employee_id=employee_id,
            role_id=role_id,
            hourly_rate=entity.hourly_rate,
            contract_hours_per_week=entity.contract_hours_per_week,
        )
        return EmployeeRoleOut.model_validate(model)

    @staticmethod
    def get_active_role(employee_id: int) -> EmployeeRoleOut | None:
        model = EmployeeRoleModel.objects.filter(
            employee_id=employee_id,
            left_at__isnull=True,
        ).first()
        return EmployeeRoleOut.model_validate(model) if model else None

    @staticmethod
    def list_role_assignments(employee_id: int) -> list[EmployeeRoleOut]:
        return [
            EmployeeRoleOut.model_validate(m)
            for m in EmployeeRoleModel.objects.filter(employee_id=employee_id).order_by(
                "assigned_at"
            )
        ]

    @staticmethod
    def close_active_role(employee_id: int, reason: str) -> EmployeeRoleOut | None:
        rows = EmployeeRoleModel.objects.filter(
            employee_id=employee_id,
            left_at__isnull=True,
        ).update(left_at=timezone.now(), left_reason=reason)
        if rows == 0:
            return None
        model = (
            EmployeeRoleModel.objects.filter(employee_id=employee_id)
            .order_by("-assigned_at")
            .first()
        )
        return EmployeeRoleOut.model_validate(model)
