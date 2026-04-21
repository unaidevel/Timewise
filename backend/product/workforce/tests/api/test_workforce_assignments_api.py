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
from product.workforce.dtos.dtos import (
    AssignDepartmentRequest,
    AssignRoleRequest,
    DepartmentIn,
    EmployeeIn,
    RoleIn,
)
from product.workforce.repositories.workforce_repository import WorkforceRepository

EXPECTED_DEFAULT_ROLE_NAMES = ["Manager", "Employee", "Intern", "Freelance"]


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


class WorkforceApiAdditionalTests(TestCase):
    def _authenticate_user(self, *, email: str, full_name: str):
        auth_router.register(
            RegisterRequest(
                email=email,
                full_name=full_name,
                password="SecurePass123!",
            )
        )
        login_response = auth_router.login_user(
            LoginRequest(email=email, password="SecurePass123!"),
            build_request("/api/v1/auth/login"),
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=login_response.access_token,
        )
        return get_current_user(credentials)

    def setUp(self):
        self.user = self._authenticate_user(
            email="owner@example.com",
            full_name="Owner",
        )
        self.tenant = tenants_router.create_tenant(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=self.user,
        )

    def _create_department(self, name: str = "Engineering"):
        return workforce_router.create_department(
            self.tenant.id,
            DepartmentIn(name=name),
            self.user,
        )

    def _create_role(self, name: str = "Developer"):
        return workforce_router.create_role(
            self.tenant.id,
            RoleIn(name=name),
            self.user,
        )

    def _employee_payload(
        self,
        department_id: int,
        role_id: int,
        *,
        email: str = "alice@example.com",
        full_name: str = "Alice Smith",
    ):
        return EmployeeIn(
            full_name=full_name,
            email=email,
            department_id=department_id,
            role_id=role_id,
            hourly_rate=Decimal("30.00"),
            contract_hours_per_week=40,
            hired_at=date(2024, 3, 1),
        )

    def _create_employee(self):
        department = self._create_department()
        role = self._create_role()
        return workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(department.id, role.id),
            self.user,
        )

    def test_create_department_returns_422_for_invalid_name(self):
        invalid_payload = DepartmentIn.model_construct(name="   ")

        with pytest.raises(HTTPException) as exc:
            workforce_router.create_department(
                self.tenant.id, invalid_payload, self.user
            )

        assert exc.value.status_code == 422
        assert exc.value.detail == "Department name cannot be blank."

    def test_get_department_returns_department(self):
        department = self._create_department()

        result = workforce_router.get_department(
            self.tenant.id, department.id, self.user
        )

        assert result == department

    def test_deactivate_department_returns_404_when_missing(self):
        with pytest.raises(HTTPException) as exc:
            workforce_router.deactivate_department(self.tenant.id, 999, self.user)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Department 999 not found."

    def test_list_roles_returns_all_sorted(self):
        workforce_router.create_role(self.tenant.id, RoleIn(name="Zulu"), self.user)
        workforce_router.create_role(self.tenant.id, RoleIn(name="Alpha"), self.user)

        roles = workforce_router.list_roles(self.tenant.id, self.user)

        assert [role.name for role in roles] == sorted(
            [*EXPECTED_DEFAULT_ROLE_NAMES, "Alpha", "Zulu"]
        )

    def test_get_role_returns_role(self):
        role = self._create_role()

        result = workforce_router.get_role(self.tenant.id, role.id, self.user)

        assert result == role

    def test_deactivate_role_marks_inactive(self):
        role = self._create_role()

        result = workforce_router.deactivate_role(self.tenant.id, role.id, self.user)

        assert result.is_active is False

    def test_deactivate_role_returns_404_when_missing(self):
        with pytest.raises(HTTPException) as exc:
            workforce_router.deactivate_role(self.tenant.id, 999, self.user)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Role 999 not found."

    def test_create_role_returns_422_for_invalid_name(self):
        invalid_payload = RoleIn.model_construct(name="   ")

        with pytest.raises(HTTPException) as exc:
            workforce_router.create_role(self.tenant.id, invalid_payload, self.user)

        assert exc.value.status_code == 422
        assert exc.value.detail == "Role name cannot be blank."

    def test_list_employees_returns_all_sorted(self):
        department = self._create_department()
        role = self._create_role()
        workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(
                department.id,
                role.id,
                email="zara@example.com",
                full_name="Zara",
            ),
            self.user,
        )
        workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(
                department.id,
                role.id,
                email="alice@example.com",
                full_name="Alice",
            ),
            self.user,
        )

        employees = workforce_router.list_employees(self.tenant.id, self.user)

        assert [employee.full_name for employee in employees] == ["Alice", "Zara"]

    def test_get_employee_returns_employee(self):
        employee = self._create_employee()

        result = workforce_router.get_employee(self.tenant.id, employee.id, self.user)

        assert result == employee

    def test_create_employee_returns_404_when_role_missing(self):
        department = self._create_department()

        with pytest.raises(HTTPException) as exc:
            workforce_router.create_employee(
                self.tenant.id,
                self._employee_payload(department.id, 999),
                self.user,
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Role 999 not found."

    def test_create_employee_returns_422_for_invalid_domain_data(self):
        department = self._create_department()
        role = self._create_role()
        invalid_payload = EmployeeIn.model_construct(
            full_name="Alice Smith",
            email="bad-email",
            department_id=department.id,
            role_id=role.id,
            hourly_rate=Decimal("30.00"),
            contract_hours_per_week=40,
            hired_at=date(2024, 3, 1),
            user_id=None,
        )

        with pytest.raises(HTTPException) as exc:
            workforce_router.create_employee(self.tenant.id, invalid_payload, self.user)

        assert exc.value.status_code == 422
        assert "Invalid email address" in exc.value.detail

    def test_assign_department_returns_created_assignment(self):
        employee = self._create_employee()
        new_department = self._create_department("People")

        assignment = workforce_router.assign_department(
            self.tenant.id,
            employee.id,
            AssignDepartmentRequest(
                department_id=new_department.id,
                reason="Reorg",
            ),
            self.user,
        )

        history = workforce_router.list_department_history(
            self.tenant.id,
            employee.id,
            self.user,
        )

        assert assignment.department_id == new_department.id
        assert assignment.left_at is None
        assert len(history) == 2
        assert history[0].left_reason == "Reorg"
        assert history[1].department_id == new_department.id

    def test_assign_department_returns_404_when_employee_missing(self):
        department = self._create_department("People")

        with pytest.raises(HTTPException) as exc:
            workforce_router.assign_department(
                self.tenant.id,
                999,
                AssignDepartmentRequest(department_id=department.id),
                self.user,
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Employee 999 not found."

    def test_assign_department_returns_404_when_department_missing(self):
        employee = self._create_employee()

        with pytest.raises(HTTPException) as exc:
            workforce_router.assign_department(
                self.tenant.id,
                employee.id,
                AssignDepartmentRequest(department_id=999),
                self.user,
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Department 999 not found."

    def test_get_active_department_returns_current_assignment(self):
        employee = self._create_employee()
        new_department = self._create_department("People")
        workforce_router.assign_department(
            self.tenant.id,
            employee.id,
            AssignDepartmentRequest(department_id=new_department.id, reason="Reorg"),
            self.user,
        )

        assignment = workforce_router.get_active_department(
            self.tenant.id,
            employee.id,
            self.user,
        )

        assert assignment.department_id == new_department.id
        assert assignment.left_at is None

    def test_get_active_department_returns_404_when_missing(self):
        employee = self._create_employee()
        WorkforceRepository.close_active_department(employee.id, "Left")

        with pytest.raises(HTTPException) as exc:
            workforce_router.get_active_department(
                self.tenant.id, employee.id, self.user
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == (
            f"Employee {employee.id} has no active department assignment."
        )

    def test_list_department_history_returns_404_when_employee_missing(self):
        with pytest.raises(HTTPException) as exc:
            workforce_router.list_department_history(self.tenant.id, 999, self.user)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Employee 999 not found."

    def test_assign_role_returns_created_assignment(self):
        employee = self._create_employee()
        new_role = self._create_role("Director")

        assignment = workforce_router.assign_role(
            self.tenant.id,
            employee.id,
            AssignRoleRequest(
                role_id=new_role.id,
                hourly_rate=Decimal("45.00"),
                contract_hours_per_week=35,
                reason="Promotion",
            ),
            self.user,
        )

        history = workforce_router.list_role_history(
            self.tenant.id,
            employee.id,
            self.user,
        )

        assert assignment.role_id == new_role.id
        assert assignment.hourly_rate == Decimal("45.00")
        assert assignment.contract_hours_per_week == 35
        assert len(history) == 2
        assert history[0].left_reason == "Promotion"
        assert history[1].role_id == new_role.id

    def test_assign_role_returns_404_when_employee_missing(self):
        role = self._create_role("Director")

        with pytest.raises(HTTPException) as exc:
            workforce_router.assign_role(
                self.tenant.id,
                999,
                AssignRoleRequest(
                    role_id=role.id,
                    hourly_rate=Decimal("45.00"),
                    contract_hours_per_week=35,
                ),
                self.user,
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Employee 999 not found."

    def test_assign_role_returns_404_when_role_missing(self):
        employee = self._create_employee()

        with pytest.raises(HTTPException) as exc:
            workforce_router.assign_role(
                self.tenant.id,
                employee.id,
                AssignRoleRequest(
                    role_id=999,
                    hourly_rate=Decimal("45.00"),
                    contract_hours_per_week=35,
                ),
                self.user,
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Role 999 not found."

    def test_assign_role_returns_404_for_invalid_assignment_data(self):
        employee = self._create_employee()
        role = self._create_role("Director")
        invalid_payload = AssignRoleRequest.model_construct(
            role_id=role.id,
            hourly_rate=Decimal("0"),
            contract_hours_per_week=35,
            reason="Invalid",
        )

        with pytest.raises(HTTPException) as exc:
            workforce_router.assign_role(
                self.tenant.id,
                employee.id,
                invalid_payload,
                self.user,
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Hourly rate must be greater than zero."

    def test_get_active_role_returns_current_assignment(self):
        employee = self._create_employee()
        new_role = self._create_role("Director")
        workforce_router.assign_role(
            self.tenant.id,
            employee.id,
            AssignRoleRequest(
                role_id=new_role.id,
                hourly_rate=Decimal("45.00"),
                contract_hours_per_week=35,
                reason="Promotion",
            ),
            self.user,
        )

        assignment = workforce_router.get_active_role(
            self.tenant.id,
            employee.id,
            self.user,
        )

        assert assignment.role_id == new_role.id
        assert assignment.hourly_rate == Decimal("45.00")
        assert assignment.contract_hours_per_week == 35

    def test_get_active_role_returns_404_when_missing(self):
        employee = self._create_employee()
        WorkforceRepository.close_active_role(employee.id, "Left")

        with pytest.raises(HTTPException) as exc:
            workforce_router.get_active_role(self.tenant.id, employee.id, self.user)

        assert exc.value.status_code == 404
        assert (
            exc.value.detail == f"Employee {employee.id} has no active role assignment."
        )

    def test_list_role_history_returns_404_when_employee_missing(self):
        with pytest.raises(HTTPException) as exc:
            workforce_router.list_role_history(self.tenant.id, 999, self.user)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Employee 999 not found."
