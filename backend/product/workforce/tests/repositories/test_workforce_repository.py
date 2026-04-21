from datetime import date

import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.tenants.dtos.dtos import TenantIn
from infra.tenants.services.tenants_service import TenantService
from product.workforce.entities.workforce_entities import (
    DepartmentEntity,
    EmployeeEntity,
    RoleEntity,
)
from product.workforce.repositories.workforce_repository import WorkforceRepository


def make_user(email: str = "owner@example.com"):
    return AuthRepository.create_user(
        email=email,
        full_name="Test User",
        password_hash=AuthService._hash_password("SecurePass123!"),
    )


def make_tenant(user_id: int, slug: str = "acme"):
    return TenantService.create(
        TenantIn(name="Acme Corp", slug=slug), created_by_id=user_id
    )


class DepartmentRepositoryTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)

    def test_create_and_get_department(self):
        entity = DepartmentEntity(name="Engineering")
        dept = WorkforceRepository.create_department(entity, self.tenant.id)

        assert dept.id is not None
        assert dept.name == "Engineering"
        assert dept.tenant_id == self.tenant.id
        assert dept.is_active is True

        found = WorkforceRepository.get_department_by_id(dept.id)
        assert found == dept

    def test_get_department_by_id_returns_none_if_missing(self):
        result = WorkforceRepository.get_department_by_id(999)
        assert result is None

    def test_find_department_by_name_is_case_insensitive(self):
        entity = DepartmentEntity(name="Engineering")
        WorkforceRepository.create_department(entity, self.tenant.id)

        found = WorkforceRepository.find_department_by_name(
            self.tenant.id, "ENGINEERING"
        )
        assert found is not None
        assert found.name == "Engineering"

    def test_find_department_by_name_returns_none_if_missing(self):
        result = WorkforceRepository.find_department_by_name(self.tenant.id, "HR")
        assert result is None

    def test_list_departments_orders_by_name(self):
        WorkforceRepository.create_department(
            DepartmentEntity(name="Zulu"), self.tenant.id
        )
        WorkforceRepository.create_department(
            DepartmentEntity(name="Alpha"), self.tenant.id
        )

        depts = WorkforceRepository.list_departments(self.tenant.id)
        assert [d.name for d in depts] == ["Alpha", "Zulu"]

    def test_deactivate_department_sets_inactive(self):
        entity = DepartmentEntity(name="Engineering")
        dept = WorkforceRepository.create_department(entity, self.tenant.id)

        result = WorkforceRepository.deactivate_department(dept.id)
        assert result is not None
        assert result.is_active is False

    def test_deactivate_department_returns_none_if_already_inactive(self):
        entity = DepartmentEntity(name="Engineering")
        dept = WorkforceRepository.create_department(entity, self.tenant.id)
        WorkforceRepository.deactivate_department(dept.id)

        result = WorkforceRepository.deactivate_department(dept.id)
        assert result is None

    def test_create_raises_type_error_if_not_entity(self):
        with pytest.raises(TypeError, match="Expected DepartmentEntity"):
            WorkforceRepository.create_department("not an entity", self.tenant.id)


class RoleRepositoryTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)

    def test_create_and_get_role(self):
        entity = RoleEntity(name="Developer")
        role = WorkforceRepository.create_role(entity, self.tenant.id)

        assert role.id is not None
        assert role.name == "Developer"
        assert role.tenant_id == self.tenant.id

        found = WorkforceRepository.get_role_by_id(role.id)
        assert found == role

    def test_get_role_by_id_returns_none_if_missing(self):
        assert WorkforceRepository.get_role_by_id(999) is None

    def test_find_role_by_name_is_case_insensitive(self):
        WorkforceRepository.create_role(RoleEntity(name="Developer"), self.tenant.id)
        found = WorkforceRepository.find_role_by_name(self.tenant.id, "DEVELOPER")
        assert found is not None

    def test_deactivate_role_sets_inactive(self):
        role = WorkforceRepository.create_role(
            RoleEntity(name="Developer"), self.tenant.id
        )
        result = WorkforceRepository.deactivate_role(role.id)
        assert result is not None
        assert result.is_active is False


class EmployeeRepositoryTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        self.dept = WorkforceRepository.create_department(
            DepartmentEntity(name="Engineering"), self.tenant.id
        )
        self.role = WorkforceRepository.create_role(
            RoleEntity(name="Developer"), self.tenant.id
        )

    def _employee_entity(self, email: str = "alice@example.com"):
        return EmployeeEntity(
            full_name="Alice Smith",
            email=email,
            hired_at=date(2024, 3, 1),
        )

    def test_create_and_get_employee(self):
        entity = self._employee_entity()
        emp = WorkforceRepository.create_employee(entity, self.tenant.id)

        assert emp.id is not None
        assert emp.email == "alice@example.com"
        assert emp.tenant_id == self.tenant.id
        assert emp.is_active is True
        assert emp.user_id is None

        found = WorkforceRepository.get_employee_by_id(emp.id)
        assert found == emp

    def test_find_employee_by_email(self):
        entity = self._employee_entity()
        WorkforceRepository.create_employee(entity, self.tenant.id)

        found = WorkforceRepository.find_employee_by_email(
            self.tenant.id, "alice@example.com"
        )
        assert found is not None
        assert found.email == "alice@example.com"

    def test_find_employee_by_email_returns_none_if_missing(self):
        result = WorkforceRepository.find_employee_by_email(
            self.tenant.id, "nobody@example.com"
        )
        assert result is None

    def test_deactivate_employee_sets_inactive(self):
        emp = WorkforceRepository.create_employee(
            self._employee_entity(), self.tenant.id
        )
        result = WorkforceRepository.deactivate_employee(emp.id)
        assert result is not None
        assert result.is_active is False

    def test_deactivate_employee_returns_none_if_already_inactive(self):
        emp = WorkforceRepository.create_employee(
            self._employee_entity(), self.tenant.id
        )
        WorkforceRepository.deactivate_employee(emp.id)
        result = WorkforceRepository.deactivate_employee(emp.id)
        assert result is None
