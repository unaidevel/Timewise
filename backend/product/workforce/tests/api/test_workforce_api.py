from datetime import date
from decimal import Decimal

import pytest
from django.test import TestCase
from django.utils import timezone
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
    AssignDepartmentManagerRequest,
    AssignDepartmentRequest,
    AssignRoleRequest,
    DepartmentIn,
    DepartmentUpdate,
    EmployeeIn,
    EmployeeUpdate,
    LinkEmployeeUserRequest,
    RemoveDepartmentManagerRequest,
    RoleIn,
    RoleUpdate,
    SetEmployeeManagerRequest,
)
from product.workforce.repositories.workforce_repository import WorkforceRepository

EXPECTED_DEFAULT_ROLE_NAMES = ["Manager", "Employee", "Intern", "Freelance"]


def build_request(
    path: str = "/api/v1/auth/login", client_host: str = "127.0.0.1"
) -> Request:
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
            RegisterRequest(
                email=email, full_name=full_name, password="SecurePass123!"
            ),
            build_request("/api/v1/auth/register"),
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
        self.tenant = tenants_router.create(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=self.user,
            request=build_request(),
        )

    # --- Departments ---

    def test_create_department_returns_201(self):
        dept = workforce_router.create_department(
            self.tenant.id,
            DepartmentIn(name="Engineering"),
            self.user,
            request=build_request(),
        )
        assert dept.name == "Engineering"
        assert dept.tenant_id == self.tenant.id

    def test_create_department_returns_409_on_duplicate(self):
        workforce_router.create_department(
            self.tenant.id,
            DepartmentIn(name="Engineering"),
            self.user,
            request=build_request(),
        )

        with pytest.raises(HTTPException) as exc:
            workforce_router.create_department(
                self.tenant.id,
                DepartmentIn(name="Engineering"),
                self.user,
                request=build_request(),
            )

        assert exc.value.status_code == 409

    def test_list_departments_returns_all(self):
        workforce_router.create_department(
            self.tenant.id,
            DepartmentIn(name="HR"),
            self.user,
            request=build_request(),
        )
        workforce_router.create_department(
            self.tenant.id,
            DepartmentIn(name="Engineering"),
            self.user,
            request=build_request(),
        )

        depts = workforce_router.list_departments(
            self.tenant.id, self.user, request=build_request()
        )
        assert len(depts) == 2
        assert [d.name for d in depts] == ["Engineering", "HR"]

    def test_get_department_returns_404_when_missing(self):
        with pytest.raises(HTTPException) as exc:
            workforce_router.get_department(
                self.tenant.id, 999, self.user, request=build_request()
            )
        assert exc.value.status_code == 404

    def test_deactivate_department_marks_inactive(self):
        dept = workforce_router.create_department(
            self.tenant.id,
            DepartmentIn(name="Engineering"),
            self.user,
            request=build_request(),
        )
        result = workforce_router.deactivate_department(
            self.tenant.id,
            dept.id,
            self.user,
            request=build_request(),
        )
        assert result.is_active is False

    # --- Roles ---

    def test_create_role_returns_201(self):
        role = workforce_router.create_role(
            self.tenant.id,
            RoleIn(name="Developer"),
            self.user,
            request=build_request(),
        )
        assert role.name == "Developer"
        assert role.tenant_id == self.tenant.id

    def test_create_role_returns_409_on_duplicate(self):
        workforce_router.create_role(
            self.tenant.id,
            RoleIn(name="Developer"),
            self.user,
            request=build_request(),
        )

        with pytest.raises(HTTPException) as exc:
            workforce_router.create_role(
                self.tenant.id,
                RoleIn(name="Developer"),
                self.user,
                request=build_request(),
            )

        assert exc.value.status_code == 409

    def test_get_role_returns_404_when_missing(self):
        with pytest.raises(HTTPException) as exc:
            workforce_router.get_role(
                self.tenant.id, 999, self.user, request=build_request()
            )
        assert exc.value.status_code == 404

    # --- Employees ---

    def _create_dept_and_role(self):
        dept = workforce_router.create_department(
            self.tenant.id,
            DepartmentIn(name="Engineering"),
            self.user,
            request=build_request(),
        )
        role = workforce_router.create_role(
            self.tenant.id,
            RoleIn(name="Developer"),
            self.user,
            request=build_request(),
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
            self.tenant.id,
            self._employee_payload(dept.id, role.id),
            self.user,
            request=build_request(),
        )
        assert emp.email == "alice@example.com"
        assert emp.is_active is True

    def test_create_employee_returns_409_on_duplicate_email(self):
        dept, role = self._create_dept_and_role()
        workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(dept.id, role.id),
            self.user,
            request=build_request(),
        )

        with pytest.raises(HTTPException) as exc:
            workforce_router.create_employee(
                self.tenant.id,
                self._employee_payload(dept.id, role.id),
                self.user,
                request=build_request(),
            )

        assert exc.value.status_code == 409

    def test_create_employee_returns_404_when_department_missing(self):
        _, role = self._create_dept_and_role()

        with pytest.raises(HTTPException) as exc:
            workforce_router.create_employee(
                self.tenant.id,
                self._employee_payload(999, role.id),
                self.user,
                request=build_request(),
            )

        assert exc.value.status_code == 404

    def test_get_employee_returns_404_when_missing(self):
        with pytest.raises(HTTPException) as exc:
            workforce_router.get_employee(
                self.tenant.id, 999, self.user, request=build_request()
            )
        assert exc.value.status_code == 404

    def test_deactivate_employee_marks_inactive(self):
        dept, role = self._create_dept_and_role()
        emp = workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(dept.id, role.id),
            self.user,
            request=build_request(),
        )
        result = workforce_router.deactivate_employee(
            self.tenant.id, emp.id, self.user, request=build_request()
        )
        assert result.is_active is False

    # --- Update endpoints ---

    def test_update_department_changes_name(self):
        dept = workforce_router.create_department(
            self.tenant.id,
            DepartmentIn(name="Engineering"),
            self.user,
            request=build_request(),
        )
        updated = workforce_router.update_department(
            self.tenant.id,
            dept.id,
            DepartmentUpdate(name="R&D"),
            self.user,
            request=build_request(),
        )
        assert updated.name == "R&D"

    def test_update_department_returns_403_for_member(self):
        dept = workforce_router.create_department(
            self.tenant.id,
            DepartmentIn(name="Engineering"),
            self.user,
            request=build_request(),
        )
        member = self._authenticate_user(email="member@example.com", full_name="Member")
        with pytest.raises(HTTPException) as exc:
            workforce_router.update_department(
                self.tenant.id,
                dept.id,
                DepartmentUpdate(name="X"),
                member,
                request=build_request(),
            )
        assert exc.value.status_code == 403

    def test_update_role_changes_name(self):
        role = workforce_router.create_role(
            self.tenant.id,
            RoleIn(name="Developer"),
            self.user,
            request=build_request(),
        )
        updated = workforce_router.update_role(
            self.tenant.id,
            role.id,
            RoleUpdate(name="Senior Developer"),
            self.user,
            request=build_request(),
        )
        assert updated.name == "Senior Developer"

    def test_update_employee_changes_name(self):
        dept, role = self._create_dept_and_role()
        emp = workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(dept.id, role.id),
            self.user,
            request=build_request(),
        )
        updated = workforce_router.update_employee(
            self.tenant.id,
            emp.id,
            EmployeeUpdate(
                full_name="Alice Jones",
                email="alice@example.com",
                hired_at=date(2024, 3, 1),
            ),
            self.user,
            request=build_request(),
        )
        assert updated.full_name == "Alice Jones"

    def test_update_employee_returns_403_for_member(self):
        dept, role = self._create_dept_and_role()
        emp = workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(dept.id, role.id),
            self.user,
            request=build_request(),
        )
        member = self._authenticate_user(email="member@example.com", full_name="Member")
        with pytest.raises(HTTPException) as exc:
            workforce_router.update_employee(
                self.tenant.id,
                emp.id,
                EmployeeUpdate(
                    full_name="X", email="alice@example.com", hired_at=date(2024, 3, 1)
                ),
                member,
                request=build_request(),
            )
        assert exc.value.status_code == 403

    # --- Department manager endpoints ---

    def test_assign_department_manager_returns_201(self):
        dept, role = self._create_dept_and_role()
        emp = workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(dept.id, role.id),
            self.user,
            request=build_request(),
        )
        assignment = workforce_router.assign_department_manager(
            self.tenant.id,
            dept.id,
            AssignDepartmentManagerRequest(employee_id=emp.id),
            self.user,
            request=build_request(),
        )
        assert assignment.department_id == dept.id
        assert assignment.employee_id == emp.id

    def test_list_department_managers_returns_active(self):
        dept, role = self._create_dept_and_role()
        emp = workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(dept.id, role.id),
            self.user,
            request=build_request(),
        )
        workforce_router.assign_department_manager(
            self.tenant.id,
            dept.id,
            AssignDepartmentManagerRequest(employee_id=emp.id),
            self.user,
            request=build_request(),
        )
        managers = workforce_router.list_department_managers(
            self.tenant.id,
            dept.id,
            self.user,
            request=build_request(),
        )
        assert len(managers) == 1
        assert managers[0].employee_id == emp.id

    def test_remove_department_manager_closes_assignment(self):
        dept, role = self._create_dept_and_role()
        emp = workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(dept.id, role.id),
            self.user,
            request=build_request(),
        )
        assignment = workforce_router.assign_department_manager(
            self.tenant.id,
            dept.id,
            AssignDepartmentManagerRequest(employee_id=emp.id),
            self.user,
            request=build_request(),
        )
        removed = workforce_router.remove_department_manager(
            self.tenant.id,
            dept.id,
            assignment.id,
            RemoveDepartmentManagerRequest(reason="Done"),
            self.user,
            request=build_request(),
        )
        assert removed.left_at is not None

    # --- Employee manager endpoints ---

    def test_set_employee_manager(self):
        dept, role = self._create_dept_and_role()
        manager_emp = workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(dept.id, role.id, "manager@example.com"),
            self.user,
            request=build_request(),
        )
        emp = workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(dept.id, role.id),
            self.user,
            request=build_request(),
        )
        updated = workforce_router.set_employee_manager(
            self.tenant.id,
            emp.id,
            SetEmployeeManagerRequest(manager_id=manager_emp.id),
            self.user,
            request=build_request(),
        )
        assert updated.manager_id == manager_emp.id

    def test_get_direct_reports(self):
        dept, role = self._create_dept_and_role()
        manager_emp = workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(dept.id, role.id, "manager@example.com"),
            self.user,
            request=build_request(),
        )
        emp = workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(dept.id, role.id),
            self.user,
            request=build_request(),
        )
        workforce_router.set_employee_manager(
            self.tenant.id,
            emp.id,
            SetEmployeeManagerRequest(manager_id=manager_emp.id),
            self.user,
            request=build_request(),
        )
        reports = workforce_router.get_direct_reports(
            self.tenant.id,
            manager_emp.id,
            self.user,
            request=build_request(),
        )
        assert len(reports) == 1
        assert reports[0].id == emp.id

    # --- Link user endpoint ---

    def test_link_employee_user_sets_user_id(self):
        dept, role = self._create_dept_and_role()
        emp = workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(dept.id, role.id),
            self.user,
            request=build_request(),
        )
        new_user = self._authenticate_user(email="alice@acme.io", full_name="Alice")

        linked = workforce_router.link_employee_user(
            self.tenant.id,
            emp.id,
            LinkEmployeeUserRequest(user_id=new_user.id),
            self.user,
            request=build_request(),
        )

        assert linked.user_id == new_user.id

    def test_link_employee_user_returns_404_when_employee_missing(self):
        new_user = self._authenticate_user(email="bob@acme.io", full_name="Bob")
        with pytest.raises(HTTPException) as exc:
            workforce_router.link_employee_user(
                self.tenant.id,
                999,
                LinkEmployeeUserRequest(user_id=new_user.id),
                self.user,
                request=build_request(),
            )
        assert exc.value.status_code == 404

    def test_link_employee_user_returns_409_when_employee_already_linked(self):
        dept, role = self._create_dept_and_role()
        first_user = self._authenticate_user(email="carol@acme.io", full_name="Carol")
        emp = workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(dept.id, role.id),
            self.user,
            request=build_request(),
        )
        workforce_router.link_employee_user(
            self.tenant.id,
            emp.id,
            LinkEmployeeUserRequest(user_id=first_user.id),
            self.user,
            request=build_request(),
        )

        second_user = self._authenticate_user(email="dave@acme.io", full_name="Dave")
        with pytest.raises(HTTPException) as exc:
            workforce_router.link_employee_user(
                self.tenant.id,
                emp.id,
                LinkEmployeeUserRequest(user_id=second_user.id),
                self.user,
                request=build_request(),
            )
        assert exc.value.status_code == 409

    def test_link_employee_user_returns_409_when_user_already_linked_to_other(self):
        dept, role = self._create_dept_and_role()
        new_user = self._authenticate_user(email="eve@acme.io", full_name="Eve")
        first_emp = workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(dept.id, role.id, "first@acme.io"),
            self.user,
            request=build_request(),
        )
        workforce_router.link_employee_user(
            self.tenant.id,
            first_emp.id,
            LinkEmployeeUserRequest(user_id=new_user.id),
            self.user,
            request=build_request(),
        )
        second_emp = workforce_router.create_employee(
            self.tenant.id,
            self._employee_payload(dept.id, role.id, "second@acme.io"),
            self.user,
            request=build_request(),
        )

        with pytest.raises(HTTPException) as exc:
            workforce_router.link_employee_user(
                self.tenant.id,
                second_emp.id,
                LinkEmployeeUserRequest(user_id=new_user.id),
                self.user,
                request=build_request(),
            )
        assert exc.value.status_code == 409


class WorkforceApiAdditionalTests(TestCase):
    def _authenticate_user(self, *, email: str, full_name: str):
        auth_router.register(
            RegisterRequest(
                email=email,
                full_name=full_name,
                password="SecurePass123!",
            ),
            build_request("/api/v1/auth/register"),
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
        self.tenant = tenants_router.create(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=self.user,
            request=build_request(),
        )

    def _create_department(self, name: str = "Engineering"):
        return workforce_router.create_department(
            self.tenant.id,
            DepartmentIn(name=name),
            self.user,
            request=build_request(),
        )

    def _create_role(self, name: str = "Developer"):
        return workforce_router.create_role(
            self.tenant.id,
            RoleIn(name=name),
            self.user,
            request=build_request(),
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
            request=build_request(),
        )

    def test_create_department_returns_422_for_invalid_name(self):
        invalid_payload = DepartmentIn.model_construct(name="   ")

        with pytest.raises(HTTPException) as exc:
            workforce_router.create_department(
                self.tenant.id,
                invalid_payload,
                self.user,
                request=build_request(),
            )

        assert exc.value.status_code == 422
        assert exc.value.detail == "Department name cannot be blank."

    def test_get_department_returns_department(self):
        department = self._create_department()

        result = workforce_router.get_department(
            self.tenant.id,
            department.id,
            self.user,
            request=build_request(),
        )

        assert result == department

    def test_deactivate_department_returns_404_when_missing(self):
        with pytest.raises(HTTPException) as exc:
            workforce_router.deactivate_department(
                self.tenant.id, 999, self.user, request=build_request()
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Department 999 not found."

    def test_list_roles_returns_all_sorted(self):
        workforce_router.create_role(
            self.tenant.id, RoleIn(name="Zulu"), self.user, request=build_request()
        )
        workforce_router.create_role(
            self.tenant.id, RoleIn(name="Alpha"), self.user, request=build_request()
        )

        roles = workforce_router.list_roles(
            self.tenant.id, self.user, request=build_request()
        )

        assert [role.name for role in roles] == sorted(
            [*EXPECTED_DEFAULT_ROLE_NAMES, "Alpha", "Zulu"]
        )

    def test_get_role_returns_role(self):
        role = self._create_role()

        result = workforce_router.get_role(
            self.tenant.id, role.id, self.user, request=build_request()
        )

        assert result == role

    def test_deactivate_role_marks_inactive(self):
        role = self._create_role()

        result = workforce_router.deactivate_role(
            self.tenant.id, role.id, self.user, request=build_request()
        )

        assert result.is_active is False

    def test_deactivate_role_returns_404_when_missing(self):
        with pytest.raises(HTTPException) as exc:
            workforce_router.deactivate_role(
                self.tenant.id, 999, self.user, request=build_request()
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Role 999 not found."

    def test_create_role_returns_422_for_invalid_name(self):
        invalid_payload = RoleIn.model_construct(name="   ")

        with pytest.raises(HTTPException) as exc:
            workforce_router.create_role(
                self.tenant.id, invalid_payload, self.user, request=build_request()
            )

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
            request=build_request(),
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
            request=build_request(),
        )

        employees = workforce_router.list_employees(
            self.tenant.id, self.user, request=build_request()
        )

        assert [employee.full_name for employee in employees] == ["Alice", "Zara"]

    def test_get_employee_returns_employee(self):
        employee = self._create_employee()

        result = workforce_router.get_employee(
            self.tenant.id, employee.id, self.user, request=build_request()
        )

        assert result == employee

    def test_create_employee_returns_404_when_role_missing(self):
        department = self._create_department()

        with pytest.raises(HTTPException) as exc:
            workforce_router.create_employee(
                self.tenant.id,
                self._employee_payload(department.id, 999),
                self.user,
                request=build_request(),
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
            workforce_router.create_employee(
                self.tenant.id, invalid_payload, self.user, request=build_request()
            )

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
            request=build_request(),
        )

        history = workforce_router.list_department_history(
            self.tenant.id,
            employee.id,
            self.user,
            request=build_request(),
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
                request=build_request(),
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
                request=build_request(),
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
            request=build_request(),
        )

        assignment = workforce_router.get_active_department(
            self.tenant.id,
            employee.id,
            self.user,
            request=build_request(),
        )

        assert assignment.department_id == new_department.id
        assert assignment.left_at is None

    def test_get_active_department_returns_404_when_missing(self):
        employee = self._create_employee()
        WorkforceRepository.close_active_department(
            employee.id, "Left", left_at=timezone.now()
        )

        with pytest.raises(HTTPException) as exc:
            workforce_router.get_active_department(
                self.tenant.id,
                employee.id,
                self.user,
                request=build_request(),
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == (
            f"Employee {employee.id} has no active department assignment."
        )

    def test_list_department_history_returns_404_when_employee_missing(self):
        with pytest.raises(HTTPException) as exc:
            workforce_router.list_department_history(
                self.tenant.id, 999, self.user, request=build_request()
            )

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
            request=build_request(),
        )

        history = workforce_router.list_role_history(
            self.tenant.id,
            employee.id,
            self.user,
            request=build_request(),
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
                request=build_request(),
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
                request=build_request(),
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Role 999 not found."

    def test_assign_role_returns_422_for_invalid_assignment_data(self):
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
                request=build_request(),
            )

        assert exc.value.status_code == 422
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
            request=build_request(),
        )

        assignment = workforce_router.get_active_role(
            self.tenant.id,
            employee.id,
            self.user,
            request=build_request(),
        )

        assert assignment.role_id == new_role.id
        assert assignment.hourly_rate == Decimal("45.00")
        assert assignment.contract_hours_per_week == 35

    def test_get_active_role_returns_404_when_missing(self):
        employee = self._create_employee()
        WorkforceRepository.close_active_role(
            employee.id, "Left", left_at=timezone.now()
        )

        with pytest.raises(HTTPException) as exc:
            workforce_router.get_active_role(
                self.tenant.id, employee.id, self.user, request=build_request()
            )

        assert exc.value.status_code == 404
        assert (
            exc.value.detail == f"Employee {employee.id} has no active role assignment."
        )

    def test_list_role_history_returns_404_when_employee_missing(self):
        with pytest.raises(HTTPException) as exc:
            workforce_router.list_role_history(
                self.tenant.id, 999, self.user, request=build_request()
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Employee 999 not found."
