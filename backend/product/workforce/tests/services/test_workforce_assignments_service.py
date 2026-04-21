from datetime import date
from decimal import Decimal

import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.tenants.entities.tenant_entities import TenantEntity
from infra.tenants.services.tenants_service import TenantService
from product.workforce.dtos.dtos import (
    AssignDepartmentRequest,
    AssignRoleRequest,
    DepartmentIn,
    EmployeeIn,
    RoleIn,
)
from product.workforce.exceptions import (
    DepartmentNotFoundError,
    EmployeeNotFoundError,
    InvalidEmployeeDataError,
    RoleNotFoundError,
)
from product.workforce.repositories.workforce_repository import WorkforceRepository
from product.workforce.services.workforce_service import WorkforceService


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


class EmployeeCreationAssignmentServiceTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        self.department = WorkforceService.create_department(
            self.tenant.id,
            DepartmentIn(name="Engineering"),
        )
        self.role = WorkforceService.create_role(
            self.tenant.id,
            RoleIn(name="Developer"),
        )

    def test_create_employee_creates_initial_department_and_role_assignments(self):
        employee = WorkforceService.create_employee(
            self.tenant.id,
            EmployeeIn(
                full_name="Alice Smith",
                email="alice@example.com",
                department_id=self.department.id,
                role_id=self.role.id,
                hourly_rate=Decimal("30.00"),
                contract_hours_per_week=40,
                hired_at=date(2024, 3, 1),
            ),
        )

        active_department = WorkforceRepository.get_active_department(employee.id)
        active_role = WorkforceRepository.get_active_role(employee.id)

        assert active_department is not None
        assert active_department.department_id == self.department.id
        assert active_role is not None
        assert active_role.role_id == self.role.id
        assert active_role.hourly_rate == Decimal("30.00")
        assert active_role.contract_hours_per_week == 40


class DepartmentAssignmentServiceTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        self.department_one = WorkforceService.create_department(
            self.tenant.id,
            DepartmentIn(name="Engineering"),
        )
        self.department_two = WorkforceService.create_department(
            self.tenant.id,
            DepartmentIn(name="People"),
        )
        self.role = WorkforceService.create_role(
            self.tenant.id,
            RoleIn(name="Developer"),
        )
        self.employee = WorkforceService.create_employee(
            self.tenant.id,
            EmployeeIn(
                full_name="Alice Smith",
                email="alice@example.com",
                department_id=self.department_one.id,
                role_id=self.role.id,
                hourly_rate=Decimal("30.00"),
                contract_hours_per_week=40,
                hired_at=date(2024, 3, 1),
            ),
        )

    def test_assign_department_replaces_active_assignment_and_preserves_history(self):
        assignment = WorkforceService.assign_department(
            self.tenant.id,
            self.employee.id,
            AssignDepartmentRequest(
                department_id=self.department_two.id,
                reason="Reorg",
            ),
        )

        active_assignment = WorkforceService.get_active_department(
            self.tenant.id,
            self.employee.id,
        )
        history = WorkforceService.list_department_history(
            self.tenant.id,
            self.employee.id,
        )

        assert assignment.department_id == self.department_two.id
        assert assignment.left_at is None
        assert active_assignment.department_id == self.department_two.id
        assert len(history) == 2
        assert history[0].department_id == self.department_one.id
        assert history[0].left_at is not None
        assert history[0].left_reason == "Reorg"
        assert history[1].department_id == self.department_two.id
        assert history[1].left_at is None

    def test_assign_department_raises_if_employee_not_found(self):
        with pytest.raises(EmployeeNotFoundError, match="Employee 999 not found"):
            WorkforceService.assign_department(
                self.tenant.id,
                999,
                AssignDepartmentRequest(department_id=self.department_two.id),
            )

    def test_assign_department_raises_if_department_not_found(self):
        with pytest.raises(DepartmentNotFoundError, match="Department 999 not found"):
            WorkforceService.assign_department(
                self.tenant.id,
                self.employee.id,
                AssignDepartmentRequest(department_id=999),
            )

    def test_assign_department_raises_if_employee_belongs_to_other_tenant(self):
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, slug="other")
        other_department = WorkforceService.create_department(
            other_tenant.id,
            DepartmentIn(name="Other Engineering"),
        )
        other_role = WorkforceService.create_role(
            other_tenant.id,
            RoleIn(name="Other Developer"),
        )
        other_employee = WorkforceService.create_employee(
            other_tenant.id,
            EmployeeIn(
                full_name="Bob Smith",
                email="bob@example.com",
                department_id=other_department.id,
                role_id=other_role.id,
                hourly_rate=Decimal("25.00"),
                contract_hours_per_week=40,
                hired_at=date(2024, 3, 1),
            ),
        )

        with pytest.raises(
            EmployeeNotFoundError, match=f"Employee {other_employee.id} not found"
        ):
            WorkforceService.assign_department(
                self.tenant.id,
                other_employee.id,
                AssignDepartmentRequest(department_id=self.department_two.id),
            )

    def test_assign_department_raises_if_department_belongs_to_other_tenant(self):
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, slug="other")
        other_department = WorkforceService.create_department(
            other_tenant.id,
            DepartmentIn(name="Other Department"),
        )

        with pytest.raises(
            DepartmentNotFoundError,
            match=f"Department {other_department.id} not found",
        ):
            WorkforceService.assign_department(
                self.tenant.id,
                self.employee.id,
                AssignDepartmentRequest(department_id=other_department.id),
            )

    def test_get_active_department_raises_if_no_active_assignment(self):
        WorkforceRepository.close_active_department(self.employee.id, "Left")

        with pytest.raises(
            DepartmentNotFoundError,
            match=f"Employee {self.employee.id} has no active department assignment",
        ):
            WorkforceService.get_active_department(self.tenant.id, self.employee.id)

    def test_list_department_history_raises_if_employee_not_found(self):
        with pytest.raises(EmployeeNotFoundError, match="Employee 999 not found"):
            WorkforceService.list_department_history(self.tenant.id, 999)


class RoleAssignmentServiceTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        self.department = WorkforceService.create_department(
            self.tenant.id,
            DepartmentIn(name="Engineering"),
        )
        self.role_one = WorkforceService.create_role(
            self.tenant.id,
            RoleIn(name="Developer"),
        )
        self.role_two = WorkforceService.create_role(
            self.tenant.id,
            RoleIn(name="Manager"),
        )
        self.employee = WorkforceService.create_employee(
            self.tenant.id,
            EmployeeIn(
                full_name="Alice Smith",
                email="alice@example.com",
                department_id=self.department.id,
                role_id=self.role_one.id,
                hourly_rate=Decimal("30.00"),
                contract_hours_per_week=40,
                hired_at=date(2024, 3, 1),
            ),
        )

    def test_assign_role_replaces_active_assignment_and_preserves_history(self):
        assignment = WorkforceService.assign_role(
            self.tenant.id,
            self.employee.id,
            AssignRoleRequest(
                role_id=self.role_two.id,
                hourly_rate=Decimal("45.00"),
                contract_hours_per_week=35,
                reason="Promotion",
            ),
        )

        active_assignment = WorkforceService.get_active_role(
            self.tenant.id,
            self.employee.id,
        )
        history = WorkforceService.list_role_history(self.tenant.id, self.employee.id)

        assert assignment.role_id == self.role_two.id
        assert assignment.hourly_rate == Decimal("45.00")
        assert assignment.contract_hours_per_week == 35
        assert assignment.left_at is None
        assert active_assignment.role_id == self.role_two.id
        assert len(history) == 2
        assert history[0].role_id == self.role_one.id
        assert history[0].left_at is not None
        assert history[0].left_reason == "Promotion"
        assert history[1].role_id == self.role_two.id
        assert history[1].hourly_rate == Decimal("45.00")
        assert history[1].contract_hours_per_week == 35

    def test_assign_role_raises_if_employee_not_found(self):
        with pytest.raises(EmployeeNotFoundError, match="Employee 999 not found"):
            WorkforceService.assign_role(
                self.tenant.id,
                999,
                AssignRoleRequest(
                    role_id=self.role_two.id,
                    hourly_rate=Decimal("45.00"),
                    contract_hours_per_week=35,
                ),
            )

    def test_assign_role_raises_if_role_not_found(self):
        with pytest.raises(RoleNotFoundError, match="Role 999 not found"):
            WorkforceService.assign_role(
                self.tenant.id,
                self.employee.id,
                AssignRoleRequest(
                    role_id=999,
                    hourly_rate=Decimal("45.00"),
                    contract_hours_per_week=35,
                ),
            )

    def test_assign_role_raises_if_role_belongs_to_other_tenant(self):
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, slug="other")
        other_role = WorkforceService.create_role(
            other_tenant.id,
            RoleIn(name="Other Manager"),
        )

        with pytest.raises(RoleNotFoundError, match=f"Role {other_role.id} not found"):
            WorkforceService.assign_role(
                self.tenant.id,
                self.employee.id,
                AssignRoleRequest(
                    role_id=other_role.id,
                    hourly_rate=Decimal("45.00"),
                    contract_hours_per_week=35,
                ),
            )

    def test_assign_role_raises_for_invalid_role_assignment_data(self):
        invalid_payload = AssignRoleRequest.model_construct(
            role_id=self.role_two.id,
            hourly_rate=Decimal("0"),
            contract_hours_per_week=35,
            reason="Invalid",
        )

        with pytest.raises(
            InvalidEmployeeDataError,
            match="Hourly rate must be greater than zero",
        ):
            WorkforceService.assign_role(
                self.tenant.id,
                self.employee.id,
                invalid_payload,
            )

    def test_get_active_role_raises_if_no_active_assignment(self):
        WorkforceRepository.close_active_role(self.employee.id, "Left")

        with pytest.raises(
            RoleNotFoundError,
            match=f"Employee {self.employee.id} has no active role assignment",
        ):
            WorkforceService.get_active_role(self.tenant.id, self.employee.id)

    def test_list_role_history_raises_if_employee_not_found(self):
        with pytest.raises(EmployeeNotFoundError, match="Employee 999 not found"):
            WorkforceService.list_role_history(self.tenant.id, 999)
