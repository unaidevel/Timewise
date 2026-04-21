from datetime import date
from decimal import Decimal

import pytest
from django.test import TestCase
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from infra.authz.api import router as auth_router
from infra.authz.api.dependencies import get_current_user
from infra.authz.dtos.dtos import LoginRequest, RegisterRequest
from infra.tenants.api import router as tenants_router
from infra.tenants.dtos.dtos import TenantIn
from product.workforce.api import router as workforce_router
from product.workforce.dtos.dtos import DepartmentIn, EmployeeIn, RoleIn


def build_request(path: str, client_host: str = "127.0.0.1") -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": path,
            "headers": [],
            "client": (client_host, 1234),
        }
    )


class WorkforceApiTests(TestCase):
    def _authenticate_user(self, *, email: str, full_name: str):
        auth_router.register(
            RegisterRequest(email=email, full_name=full_name, password="SecurePass123!")
        )
        login_response = auth_router.login_user(
            LoginRequest(email=email, password="SecurePass123!"),
            build_request("/api/v1/auth/login"),
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=login_response.access_token
        )
        return get_current_user(credentials)

    def setUp(self):
        self.user = self._authenticate_user(
            email="owner@example.com", full_name="Owner"
        )
        self.tenant = tenants_router.create_tenant(
            TenantIn(name="Acme Corp", slug="acme"), current_user=self.user
        )

    # --- Departments ---

    def test_create_department_returns_201(self):
        dept = workforce_router.create_department(
            self.tenant.id, DepartmentIn(name="Engineering"), self.user
        )
        assert dept.name == "Engineering"
        assert dept.tenant_id == self.tenant.id

    def test_create_department_returns_409_on_duplicate(self):
        workforce_router.create_department(
            self.tenant.id, DepartmentIn(name="Engineering"), self.user
        )

        with pytest.raises(HTTPException) as exc:
            workforce_router.create_department(
                self.tenant.id, DepartmentIn(name="Engineering"), self.user
            )

        assert exc.value.status_code == 409

    def test_list_departments_returns_all(self):
        workforce_router.create_department(
            self.tenant.id, DepartmentIn(name="HR"), self.user
        )
        workforce_router.create_department(
            self.tenant.id, DepartmentIn(name="Engineering"), self.user
        )

        depts = workforce_router.list_departments(self.tenant.id, self.user)
        assert len(depts) == 2
        assert [d.name for d in depts] == ["Engineering", "HR"]

    def test_get_department_returns_404_when_missing(self):
        with pytest.raises(HTTPException) as exc:
            workforce_router.get_department(self.tenant.id, 999, self.user)
        assert exc.value.status_code == 404

    def test_deactivate_department_marks_inactive(self):
        dept = workforce_router.create_department(
            self.tenant.id, DepartmentIn(name="Engineering"), self.user
        )
        result = workforce_router.deactivate_department(
            self.tenant.id, dept.id, self.user
        )
        assert result.is_active is False

    # --- Roles ---

    def test_create_role_returns_201(self):
        role = workforce_router.create_role(
            self.tenant.id, RoleIn(name="Developer"), self.user
        )
        assert role.name == "Developer"
        assert role.tenant_id == self.tenant.id

    def test_create_role_returns_409_on_duplicate(self):
        workforce_router.create_role(
            self.tenant.id, RoleIn(name="Developer"), self.user
        )

        with pytest.raises(HTTPException) as exc:
            workforce_router.create_role(
                self.tenant.id, RoleIn(name="Developer"), self.user
            )

        assert exc.value.status_code == 409

    def test_get_role_returns_404_when_missing(self):
        with pytest.raises(HTTPException) as exc:
            workforce_router.get_role(self.tenant.id, 999, self.user)
        assert exc.value.status_code == 404

    # --- Employees ---

    def _create_dept_and_role(self):
        dept = workforce_router.create_department(
            self.tenant.id, DepartmentIn(name="Engineering"), self.user
        )
        role = workforce_router.create_role(
            self.tenant.id, RoleIn(name="Developer"), self.user
        )
        return dept, role

    def _employee_payload(
        self, dept_id: int, role_id: int, email: str = "alice@example.com"
    ):
        return EmployeeIn(
            full_name="Alice Smith",
            email=email,
            department_id=dept_id,
            role_id=role_id,
            hourly_rate=Decimal("30.00"),
            contract_hours_per_week=40,
            hired_at=date(2024, 3, 1),
        )

    def test_create_employee_returns_201(self):
        dept, role = self._create_dept_and_role()
        emp = workforce_router.create_employee(
            self.tenant.id, self._employee_payload(dept.id, role.id), self.user
        )
        assert emp.email == "alice@example.com"
        assert emp.is_active is True

    def test_create_employee_returns_409_on_duplicate_email(self):
        dept, role = self._create_dept_and_role()
        workforce_router.create_employee(
            self.tenant.id, self._employee_payload(dept.id, role.id), self.user
        )

        with pytest.raises(HTTPException) as exc:
            workforce_router.create_employee(
                self.tenant.id, self._employee_payload(dept.id, role.id), self.user
            )

        assert exc.value.status_code == 409

    def test_create_employee_returns_404_when_department_missing(self):
        _, role = self._create_dept_and_role()

        with pytest.raises(HTTPException) as exc:
            workforce_router.create_employee(
                self.tenant.id, self._employee_payload(999, role.id), self.user
            )

        assert exc.value.status_code == 404

    def test_get_employee_returns_404_when_missing(self):
        with pytest.raises(HTTPException) as exc:
            workforce_router.get_employee(self.tenant.id, 999, self.user)
        assert exc.value.status_code == 404

    def test_deactivate_employee_marks_inactive(self):
        dept, role = self._create_dept_and_role()
        emp = workforce_router.create_employee(
            self.tenant.id, self._employee_payload(dept.id, role.id), self.user
        )
        result = workforce_router.deactivate_employee(self.tenant.id, emp.id, self.user)
        assert result.is_active is False
