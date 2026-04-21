from datetime import date
from decimal import Decimal

import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.tenants.entities.tenant_entities import TenantEntity
from infra.tenants.services.tenants_service import TenantService
from product.workforce.entities.workforce_entities import (
    DepartmentEntity,
    EmployeeEntity,
    EmployeeRoleEntity,
    RoleEntity,
)
from product.workforce.repositories.workforce_repository import WorkforceRepository

EXPECTED_DEFAULT_ROLE_NAMES = ["Manager", "Employee", "Intern", "Freelance"]


def make_user(email: str = "owner@example.com"):
    return AuthRepository.create_user(
        email=email,
        full_name="Test User",
        password_hash=AuthService._hash_password("SecurePass123!"),
    )


def make_tenant(user_id: int, slug: str = "acme"):
    return TenantService.create(
        TenantEntity(name="Acme Corp", slug=slug), created_by_id=user_id
    )


class RoleRepositoryAdditionalTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)

    def test_list_roles_orders_by_name(self):
        WorkforceRepository.create_role(RoleEntity(name="Zulu"), self.tenant.id)
        WorkforceRepository.create_role(RoleEntity(name="Alpha"), self.tenant.id)

        roles = WorkforceRepository.list_roles(self.tenant.id)

        assert [role.name for role in roles] == ["Alpha", "Zulu"]

    def test_create_default_roles_returns_created_roles(self):
        roles = WorkforceRepository._create_default_roles(self.tenant.id)

        assert len(roles) == len(EXPECTED_DEFAULT_ROLE_NAMES)
        assert {role.name for role in roles} == set(EXPECTED_DEFAULT_ROLE_NAMES)
        assert all(role.tenant_id == self.tenant.id for role in roles)
        assert all(role.is_active is True for role in roles)

    def test_create_role_raises_type_error_if_not_entity(self):
        with pytest.raises(TypeError, match="Expected RoleEntity"):
            WorkforceRepository.create_role("not an entity", self.tenant.id)

    def test_deactivate_role_returns_none_if_already_inactive(self):
        role = WorkforceRepository.create_role(
            RoleEntity(name="Developer"), self.tenant.id
        )
        WorkforceRepository.deactivate_role(role.id)

        result = WorkforceRepository.deactivate_role(role.id)

        assert result is None


class EmployeeRepositoryAdditionalTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.profile_user = make_user("employee@example.com")
        self.tenant = make_tenant(self.user.id)

    def _employee_entity(
        self, full_name: str = "Alice Smith", email: str = "alice@example.com"
    ):
        return EmployeeEntity(
            full_name=full_name,
            email=email,
            hired_at=date(2024, 3, 1),
        )

    def test_create_employee_persists_user_id_when_provided(self):
        employee = WorkforceRepository.create_employee(
            self._employee_entity(),
            self.tenant.id,
            user_id=self.profile_user.id,
        )

        assert employee.user_id == self.profile_user.id

    def test_create_employee_raises_type_error_if_not_entity(self):
        with pytest.raises(TypeError, match="Expected EmployeeEntity"):
            WorkforceRepository.create_employee("not an entity", self.tenant.id)

    def test_list_employees_orders_by_full_name(self):
        WorkforceRepository.create_employee(
            self._employee_entity(full_name="Zara", email="zara@example.com"),
            self.tenant.id,
        )
        WorkforceRepository.create_employee(
            self._employee_entity(full_name="Alice", email="alice@example.com"),
            self.tenant.id,
        )

        employees = WorkforceRepository.list_employees(self.tenant.id)

        assert [employee.full_name for employee in employees] == ["Alice", "Zara"]


class DepartmentAssignmentRepositoryTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        self.department_one = WorkforceRepository.create_department(
            DepartmentEntity(name="Engineering"),
            self.tenant.id,
        )
        self.department_two = WorkforceRepository.create_department(
            DepartmentEntity(name="People"),
            self.tenant.id,
        )
        self.employee = WorkforceRepository.create_employee(
            EmployeeEntity(
                full_name="Alice Smith",
                email="alice@example.com",
                hired_at=date(2024, 3, 1),
            ),
            self.tenant.id,
        )

    def test_get_active_department_returns_none_when_missing(self):
        assignment = WorkforceRepository.get_active_department(self.employee.id)

        assert assignment is None

    def test_assign_department_creates_active_assignment(self):
        assignment = WorkforceRepository.assign_department(
            self.employee.id,
            self.department_one.id,
        )

        active_assignment = WorkforceRepository.get_active_department(self.employee.id)

        assert assignment.employee_id == self.employee.id
        assert assignment.department_id == self.department_one.id
        assert assignment.left_at is None
        assert active_assignment == assignment

    def test_list_department_assignments_returns_history_in_order(self):
        first = WorkforceRepository.assign_department(
            self.employee.id, self.department_one.id
        )
        WorkforceRepository.close_active_department(self.employee.id, "Reorg")
        second = WorkforceRepository.assign_department(
            self.employee.id, self.department_two.id
        )

        history = WorkforceRepository.list_department_assignments(self.employee.id)

        assert [assignment.id for assignment in history] == [first.id, second.id]
        assert [assignment.department_id for assignment in history] == [
            self.department_one.id,
            self.department_two.id,
        ]

    def test_close_active_department_sets_left_at_and_reason(self):
        WorkforceRepository.assign_department(self.employee.id, self.department_one.id)

        closed_assignment = WorkforceRepository.close_active_department(
            self.employee.id,
            "Moved teams",
        )

        assert closed_assignment is not None
        assert closed_assignment.department_id == self.department_one.id
        assert closed_assignment.left_at is not None
        assert closed_assignment.left_reason == "Moved teams"
        assert WorkforceRepository.get_active_department(self.employee.id) is None

    def test_close_active_department_returns_none_when_no_active_assignment(self):
        closed_assignment = WorkforceRepository.close_active_department(
            self.employee.id,
            "Nothing to close",
        )

        assert closed_assignment is None


class RoleAssignmentRepositoryTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        self.role_one = WorkforceRepository.create_role(
            RoleEntity(name="Developer"),
            self.tenant.id,
        )
        self.role_two = WorkforceRepository.create_role(
            RoleEntity(name="Manager"),
            self.tenant.id,
        )
        self.employee = WorkforceRepository.create_employee(
            EmployeeEntity(
                full_name="Alice Smith",
                email="alice@example.com",
                hired_at=date(2024, 3, 1),
            ),
            self.tenant.id,
        )

    def test_get_active_role_returns_none_when_missing(self):
        assignment = WorkforceRepository.get_active_role(self.employee.id)

        assert assignment is None

    def test_assign_role_creates_active_assignment(self):
        assignment = WorkforceRepository.assign_role(
            self.employee.id,
            self.role_one.id,
            EmployeeRoleEntity(
                hourly_rate=Decimal("30.00"),
                contract_hours_per_week=40,
            ),
        )

        active_assignment = WorkforceRepository.get_active_role(self.employee.id)

        assert assignment.employee_id == self.employee.id
        assert assignment.role_id == self.role_one.id
        assert assignment.hourly_rate == Decimal("30.00")
        assert assignment.contract_hours_per_week == 40
        assert assignment.left_at is None
        assert active_assignment == assignment

    def test_assign_role_raises_type_error_if_not_entity(self):
        with pytest.raises(TypeError, match="Expected EmployeeRoleEntity"):
            WorkforceRepository.assign_role(
                self.employee.id,
                self.role_one.id,
                "not an entity",
            )

    def test_list_role_assignments_returns_history_in_order(self):
        first = WorkforceRepository.assign_role(
            self.employee.id,
            self.role_one.id,
            EmployeeRoleEntity(
                hourly_rate=Decimal("30.00"),
                contract_hours_per_week=40,
            ),
        )
        WorkforceRepository.close_active_role(self.employee.id, "Promotion")
        second = WorkforceRepository.assign_role(
            self.employee.id,
            self.role_two.id,
            EmployeeRoleEntity(
                hourly_rate=Decimal("45.00"),
                contract_hours_per_week=35,
            ),
        )

        history = WorkforceRepository.list_role_assignments(self.employee.id)

        assert [assignment.id for assignment in history] == [first.id, second.id]
        assert [assignment.role_id for assignment in history] == [
            self.role_one.id,
            self.role_two.id,
        ]

    def test_close_active_role_sets_left_at_and_reason(self):
        WorkforceRepository.assign_role(
            self.employee.id,
            self.role_one.id,
            EmployeeRoleEntity(
                hourly_rate=Decimal("30.00"),
                contract_hours_per_week=40,
            ),
        )

        closed_assignment = WorkforceRepository.close_active_role(
            self.employee.id,
            "Promotion",
        )

        assert closed_assignment is not None
        assert closed_assignment.role_id == self.role_one.id
        assert closed_assignment.left_at is not None
        assert closed_assignment.left_reason == "Promotion"
        assert WorkforceRepository.get_active_role(self.employee.id) is None

    def test_close_active_role_returns_none_when_no_active_assignment(self):
        closed_assignment = WorkforceRepository.close_active_role(
            self.employee.id,
            "Nothing to close",
        )

        assert closed_assignment is None
