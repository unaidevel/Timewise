from datetime import date
from decimal import Decimal

import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.tenants.entities.tenant_entities import TenantEntity
from infra.tenants.services.tenants_service import TenantService
from product.workforce.dtos.dtos import DepartmentIn, EmployeeIn, RoleIn
from product.workforce.exceptions import (
    DepartmentAlreadyExistsError,
    DepartmentNotFoundError,
    EmployeeAlreadyExistsError,
    EmployeeNotFoundError,
    InvalidEmployeeDataError,
    RoleAlreadyExistsError,
    RoleNotFoundError,
)
from product.workforce.services.workforce_service import WorkforceService

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


class DepartmentServiceTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)

    def test_create_department_normalizes_name(self):
        dept = WorkforceService.create_department(
            self.tenant.id, DepartmentIn(name="  Engineering  ")
        )
        assert dept.name == "Engineering"
        assert dept.tenant_id == self.tenant.id
        assert dept.is_active is True

    def test_create_department_raises_if_name_already_exists(self):
        WorkforceService.create_department(
            self.tenant.id, DepartmentIn(name="Engineering")
        )

        with pytest.raises(DepartmentAlreadyExistsError, match="Engineering"):
            WorkforceService.create_department(
                self.tenant.id, DepartmentIn(name="  ENGINEERING  ")
            )

    def test_create_department_allows_same_name_in_different_tenants(self):
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, slug="other")

        WorkforceService.create_department(
            self.tenant.id, DepartmentIn(name="Engineering")
        )
        dept = WorkforceService.create_department(
            other_tenant.id, DepartmentIn(name="Engineering")
        )

        assert dept.tenant_id == other_tenant.id

    def test_get_department_returns_department(self):
        created = WorkforceService.create_department(
            self.tenant.id, DepartmentIn(name="Engineering")
        )
        found = WorkforceService.get_department(self.tenant.id, created.id)
        assert found == created

    def test_get_department_raises_if_not_found(self):
        with pytest.raises(DepartmentNotFoundError, match="Department 999 not found"):
            WorkforceService.get_department(self.tenant.id, 999)

    def test_get_department_raises_if_belongs_to_other_tenant(self):
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, slug="other")
        dept = WorkforceService.create_department(
            other_tenant.id, DepartmentIn(name="HR")
        )

        with pytest.raises(DepartmentNotFoundError):
            WorkforceService.get_department(self.tenant.id, dept.id)

    def test_list_departments_returns_sorted_by_name(self):
        WorkforceService.create_department(self.tenant.id, DepartmentIn(name="Zulu"))
        WorkforceService.create_department(self.tenant.id, DepartmentIn(name="Alpha"))

        depts = WorkforceService.list_departments(self.tenant.id)
        assert [d.name for d in depts] == ["Alpha", "Zulu"]

    def test_deactivate_department_marks_inactive(self):
        dept = WorkforceService.create_department(
            self.tenant.id, DepartmentIn(name="Engineering")
        )
        result = WorkforceService.deactivate_department(self.tenant.id, dept.id)
        assert result.is_active is False

    def test_deactivate_department_raises_if_not_found(self):
        with pytest.raises(DepartmentNotFoundError):
            WorkforceService.deactivate_department(self.tenant.id, 999)


class RoleServiceTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)

    def test_create_role_normalizes_name(self):
        role = WorkforceService.create_role(
            self.tenant.id, RoleIn(name="  Senior Engineer  ")
        )
        assert role.name == "Senior Engineer"
        assert role.tenant_id == self.tenant.id

    def test_create_role_raises_if_name_already_exists(self):
        WorkforceService.create_role(self.tenant.id, RoleIn(name="Developer"))

        with pytest.raises(RoleAlreadyExistsError, match="Developer"):
            WorkforceService.create_role(self.tenant.id, RoleIn(name="  DEVELOPER  "))

    def test_get_role_returns_role(self):
        created = WorkforceService.create_role(self.tenant.id, RoleIn(name="Developer"))
        found = WorkforceService.get_role(self.tenant.id, created.id)
        assert found == created

    def test_get_role_raises_if_not_found(self):
        with pytest.raises(RoleNotFoundError, match="Role 999 not found"):
            WorkforceService.get_role(self.tenant.id, 999)

    def test_deactivate_role_marks_inactive(self):
        role = WorkforceService.create_role(self.tenant.id, RoleIn(name="Developer"))
        result = WorkforceService.deactivate_role(self.tenant.id, role.id)
        assert result.is_active is False

    def test_deactivate_role_raises_if_not_found(self):
        with pytest.raises(RoleNotFoundError):
            WorkforceService.deactivate_role(self.tenant.id, 999)


class EmployeeServiceTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        self.dept = WorkforceService.create_department(
            self.tenant.id, DepartmentIn(name="Engineering")
        )
        self.role = WorkforceService.create_role(
            self.tenant.id, RoleIn(name="Developer")
        )

    def _employee_payload(self, email: str = "alice@example.com", **overrides):
        defaults = dict(
            full_name="Alice Smith",
            email=email,
            department_id=self.dept.id,
            role_id=self.role.id,
            hourly_rate=Decimal("30.00"),
            contract_hours_per_week=40,
            hired_at=date(2024, 3, 1),
        )
        return EmployeeIn(**{**defaults, **overrides})

    def test_create_employee_stores_normalized_data(self):
        emp = WorkforceService.create_employee(
            self.tenant.id, self._employee_payload(email="  ALICE@Example.COM  ")
        )
        assert emp.email == "alice@example.com"
        assert emp.tenant_id == self.tenant.id
        assert emp.is_active is True

    def test_create_employee_raises_if_email_already_exists(self):
        WorkforceService.create_employee(self.tenant.id, self._employee_payload())

        with pytest.raises(EmployeeAlreadyExistsError, match="alice@example.com"):
            WorkforceService.create_employee(self.tenant.id, self._employee_payload())

    def test_create_employee_raises_if_department_not_found(self):
        with pytest.raises(DepartmentNotFoundError, match="Department 999"):
            WorkforceService.create_employee(
                self.tenant.id, self._employee_payload(department_id=999)
            )

    def test_create_employee_raises_if_role_not_found(self):
        with pytest.raises(RoleNotFoundError, match="Role 999"):
            WorkforceService.create_employee(
                self.tenant.id, self._employee_payload(role_id=999)
            )

    def test_create_employee_raises_on_invalid_email(self):
        with pytest.raises(InvalidEmployeeDataError, match="Invalid email"):
            WorkforceService.create_employee(
                self.tenant.id, self._employee_payload(email="bad-email")
            )

    def test_get_employee_returns_employee(self):
        emp = WorkforceService.create_employee(self.tenant.id, self._employee_payload())
        found = WorkforceService.get_employee(self.tenant.id, emp.id)
        assert found == emp

    def test_get_employee_raises_if_not_found(self):
        with pytest.raises(EmployeeNotFoundError, match="Employee 999 not found"):
            WorkforceService.get_employee(self.tenant.id, 999)

    def test_list_employees_returns_sorted_by_name(self):
        WorkforceService.create_employee(
            self.tenant.id,
            self._employee_payload("zara@example.com", full_name="Zara"),
        )
        WorkforceService.create_employee(
            self.tenant.id,
            self._employee_payload("alice@example.com", full_name="Alice"),
        )

        employees = WorkforceService.list_employees(self.tenant.id)
        assert [e.full_name for e in employees] == ["Alice", "Zara"]

    def test_deactivate_employee_marks_inactive(self):
        emp = WorkforceService.create_employee(self.tenant.id, self._employee_payload())
        result = WorkforceService.deactivate_employee(self.tenant.id, emp.id)
        assert result.is_active is False

    def test_deactivate_employee_raises_if_not_found(self):
        with pytest.raises(EmployeeNotFoundError):
            WorkforceService.deactivate_employee(self.tenant.id, 999)


class DefaultRolesServiceTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)

    def test_create_default_roles_creates_expected_roles(self):
        WorkforceService.create_default_roles(self.tenant.id)

        roles = WorkforceService.list_roles(self.tenant.id)
        assert len(roles) == len(EXPECTED_DEFAULT_ROLE_NAMES)
        assert {r.name for r in roles} == set(EXPECTED_DEFAULT_ROLE_NAMES)

    def test_create_default_roles_are_all_active(self):
        WorkforceService.create_default_roles(self.tenant.id)

        roles = WorkforceService.list_roles(self.tenant.id)
        assert all(r.is_active for r in roles)

    def test_create_default_roles_are_scoped_to_tenant(self):
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, slug="other")

        WorkforceService.create_default_roles(self.tenant.id)

        assert WorkforceService.list_roles(other_tenant.id) == []
