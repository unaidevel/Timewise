from datetime import date
from decimal import Decimal

import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.exceptions import InsufficientPermissionsError
from infra.tenants.services.tenants_service import TenantService
from product.workforce.dtos.dtos import (
    AssignDepartmentManagerRequest,
    AssignDepartmentRequest,
    AssignRoleRequest,
    DepartmentIn,
    DepartmentUpdate,
    EmployeeIn,
    EmployeeUpdate,
    RemoveDepartmentManagerRequest,
    RoleIn,
    RoleUpdate,
    SetEmployeeManagerRequest,
)
from product.workforce.exceptions import (
    DepartmentAlreadyExistsError,
    DepartmentNotFoundError,
    EmployeeAlreadyExistsError,
    EmployeeNotFoundError,
    InvalidEmployeeDataError,
    ManagerAlreadyAssignedError,
    ManagerAssignmentNotFoundError,
    RoleAlreadyExistsError,
    RoleNotFoundError,
)
from product.workforce.models import EmployeeDepartmentModel, EmployeeRoleModel
from product.workforce.repositories.workforce_repository import WorkforceRepository
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


def add_member(tenant_id: int, user_id: int, role: MembershipRoles):
    TenantService.add_membership(
        tenant_id=tenant_id,
        user_id=user_id,
        entity=TenantMembershipEntity(role=role.value),
        invited_by_id=None,
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


class UpdateDepartmentServiceTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.tenant = make_tenant(self.owner.id)
        add_member(self.tenant.id, self.owner.id, MembershipRoles.OWNER)
        self.dept = WorkforceService.create_department(
            self.tenant.id, DepartmentIn(name="Engineering")
        )

    def test_update_department_renames(self):
        updated = WorkforceService.update_department(
            self.tenant.id,
            self.dept.id,
            DepartmentUpdate(name="R&D"),
            user_id=self.owner.id,
        )
        assert updated.name == "R&D"
        assert updated.id == self.dept.id

    def test_update_department_normalizes_name(self):
        updated = WorkforceService.update_department(
            self.tenant.id,
            self.dept.id,
            DepartmentUpdate(name="  R&D  "),
            user_id=self.owner.id,
        )
        assert updated.name == "R&D"

    def test_update_department_raises_if_not_found(self):
        with pytest.raises(DepartmentNotFoundError):
            WorkforceService.update_department(
                self.tenant.id, 999, DepartmentUpdate(name="X"), user_id=self.owner.id
            )

    def test_update_department_raises_if_name_conflicts(self):
        WorkforceService.create_department(self.tenant.id, DepartmentIn(name="HR"))
        with pytest.raises(DepartmentAlreadyExistsError):
            WorkforceService.update_department(
                self.tenant.id,
                self.dept.id,
                DepartmentUpdate(name="HR"),
                user_id=self.owner.id,
            )

    def test_update_department_allows_rename_to_same_name(self):
        updated = WorkforceService.update_department(
            self.tenant.id,
            self.dept.id,
            DepartmentUpdate(name="Engineering"),
            user_id=self.owner.id,
        )
        assert updated.name == "Engineering"

    def test_update_department_raises_on_insufficient_permissions(self):
        member = make_user("member@example.com")
        add_member(self.tenant.id, member.id, MembershipRoles.MEMBER)
        with pytest.raises(InsufficientPermissionsError):
            WorkforceService.update_department(
                self.tenant.id,
                self.dept.id,
                DepartmentUpdate(name="X"),
                user_id=member.id,
            )


class UpdateRoleServiceTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.tenant = make_tenant(self.owner.id)
        add_member(self.tenant.id, self.owner.id, MembershipRoles.OWNER)
        self.role = WorkforceService.create_role(
            self.tenant.id, RoleIn(name="Developer")
        )

    def test_update_role_renames(self):
        updated = WorkforceService.update_role(
            self.tenant.id,
            self.role.id,
            RoleUpdate(name="Senior Developer"),
            user_id=self.owner.id,
        )
        assert updated.name == "Senior Developer"

    def test_update_role_raises_if_not_found(self):
        with pytest.raises(RoleNotFoundError):
            WorkforceService.update_role(
                self.tenant.id, 999, RoleUpdate(name="X"), user_id=self.owner.id
            )

    def test_update_role_raises_if_name_conflicts(self):
        WorkforceService.create_role(self.tenant.id, RoleIn(name="QA"))
        with pytest.raises(RoleAlreadyExistsError):
            WorkforceService.update_role(
                self.tenant.id,
                self.role.id,
                RoleUpdate(name="QA"),
                user_id=self.owner.id,
            )

    def test_update_role_raises_on_insufficient_permissions(self):
        member = make_user("member@example.com")
        add_member(self.tenant.id, member.id, MembershipRoles.MEMBER)
        with pytest.raises(InsufficientPermissionsError):
            WorkforceService.update_role(
                self.tenant.id, self.role.id, RoleUpdate(name="X"), user_id=member.id
            )


class UpdateEmployeeServiceTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.tenant = make_tenant(self.owner.id)
        add_member(self.tenant.id, self.owner.id, MembershipRoles.OWNER)
        dept = WorkforceService.create_department(
            self.tenant.id, DepartmentIn(name="Eng")
        )
        role = WorkforceService.create_role(self.tenant.id, RoleIn(name="Dev"))
        self.emp = WorkforceService.create_employee(
            self.tenant.id,
            EmployeeIn(
                full_name="Alice Smith",
                email="alice@example.com",
                department_id=dept.id,
                role_id=role.id,
                hourly_rate="30.00",
                contract_hours_per_week=40,
                hired_at=date(2024, 3, 1),
            ),
        )

    def test_update_employee_changes_name(self):
        updated = WorkforceService.update_employee(
            self.tenant.id,
            self.emp.id,
            EmployeeUpdate(full_name="Alice Jones", email="alice@example.com", hired_at=date(2024, 3, 1)),
            user_id=self.owner.id,
        )
        assert updated.full_name == "Alice Jones"
        assert updated.email == "alice@example.com"

    def test_update_employee_changes_email(self):
        updated = WorkforceService.update_employee(
            self.tenant.id,
            self.emp.id,
            EmployeeUpdate(full_name="Alice Smith", email="newalice@example.com", hired_at=date(2024, 3, 1)),
            user_id=self.owner.id,
        )
        assert updated.email == "newalice@example.com"

    def test_update_employee_raises_on_duplicate_email(self):
        dept = WorkforceService.list_departments(self.tenant.id)[0]
        role = WorkforceService.list_roles(self.tenant.id)[0]
        WorkforceService.create_employee(
            self.tenant.id,
            EmployeeIn(
                full_name="Bob",
                email="bob@example.com",
                department_id=dept.id,
                role_id=role.id,
                hourly_rate="20.00",
                contract_hours_per_week=40,
                hired_at=date(2024, 3, 1),
            ),
        )
        with pytest.raises(EmployeeAlreadyExistsError):
            WorkforceService.update_employee(
                self.tenant.id,
                self.emp.id,
                EmployeeUpdate(full_name="Alice Smith", email="bob@example.com", hired_at=date(2024, 3, 1)),
                user_id=self.owner.id,
            )

    def test_update_employee_raises_if_not_found(self):
        with pytest.raises(EmployeeNotFoundError):
            WorkforceService.update_employee(
                self.tenant.id,
                999,
                EmployeeUpdate(full_name="X", email="x@example.com", hired_at=date(2024, 3, 1)),
                user_id=self.owner.id,
            )

    def test_update_employee_raises_on_insufficient_permissions(self):
        member = make_user("member@example.com")
        add_member(self.tenant.id, member.id, MembershipRoles.MEMBER)
        with pytest.raises(InsufficientPermissionsError):
            WorkforceService.update_employee(
                self.tenant.id,
                self.emp.id,
                EmployeeUpdate(full_name="X", email="x@example.com", hired_at=date(2024, 3, 1)),
                user_id=member.id,
            )


class DeactivateEmployeeServiceTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.tenant = make_tenant(self.owner.id)
        dept = WorkforceService.create_department(
            self.tenant.id, DepartmentIn(name="Eng")
        )
        role = WorkforceService.create_role(self.tenant.id, RoleIn(name="Dev"))
        self.emp = WorkforceService.create_employee(
            self.tenant.id,
            EmployeeIn(
                full_name="Alice Smith",
                email="alice@example.com",
                department_id=dept.id,
                role_id=role.id,
                hourly_rate="30.00",
                contract_hours_per_week=40,
                hired_at=date(2024, 3, 1),
            ),
        )

    def test_deactivate_employee_also_closes_department_assignment(self):
        WorkforceService.deactivate_employee(self.tenant.id, self.emp.id)
        open_dept = EmployeeDepartmentModel.objects.filter(
            employee_id=self.emp.id, left_at__isnull=True
        )
        assert not open_dept.exists()

    def test_deactivate_employee_also_closes_role_assignment(self):
        WorkforceService.deactivate_employee(self.tenant.id, self.emp.id)
        open_role = EmployeeRoleModel.objects.filter(
            employee_id=self.emp.id, left_at__isnull=True
        )
        assert not open_role.exists()

    def test_deactivate_employee_marks_inactive(self):
        result = WorkforceService.deactivate_employee(self.tenant.id, self.emp.id)
        assert result.is_active is False


class DepartmentManagerServiceTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.tenant = make_tenant(self.owner.id)
        add_member(self.tenant.id, self.owner.id, MembershipRoles.OWNER)
        self.dept = WorkforceService.create_department(
            self.tenant.id, DepartmentIn(name="Engineering")
        )
        role = WorkforceService.create_role(self.tenant.id, RoleIn(name="Dev"))
        self.emp = WorkforceService.create_employee(
            self.tenant.id,
            EmployeeIn(
                full_name="Alice Smith",
                email="alice@example.com",
                department_id=self.dept.id,
                role_id=role.id,
                hourly_rate="30.00",
                contract_hours_per_week=40,
                hired_at=date(2024, 3, 1),
            ),
        )

    def test_assign_department_manager_creates_assignment(self):
        assignment = WorkforceService.assign_department_manager(
            self.tenant.id,
            self.dept.id,
            AssignDepartmentManagerRequest(employee_id=self.emp.id),
            user_id=self.owner.id,
        )
        assert assignment.department_id == self.dept.id
        assert assignment.employee_id == self.emp.id
        assert assignment.left_at is None

    def test_assign_department_manager_allows_multiple_active_managers(self):
        role = WorkforceService.list_roles(self.tenant.id)[0]
        emp2 = WorkforceService.create_employee(
            self.tenant.id,
            EmployeeIn(
                full_name="Bob Jones",
                email="bob@example.com",
                department_id=self.dept.id,
                role_id=role.id,
                hourly_rate="30.00",
                contract_hours_per_week=40,
                hired_at=date(2024, 3, 1),
            ),
        )
        WorkforceService.assign_department_manager(
            self.tenant.id,
            self.dept.id,
            AssignDepartmentManagerRequest(employee_id=self.emp.id),
            user_id=self.owner.id,
        )
        WorkforceService.assign_department_manager(
            self.tenant.id,
            self.dept.id,
            AssignDepartmentManagerRequest(employee_id=emp2.id),
            user_id=self.owner.id,
        )
        managers = WorkforceService.list_department_managers(
            self.tenant.id, self.dept.id
        )
        assert len(managers) == 2

    def test_assign_department_manager_raises_if_already_assigned(self):
        WorkforceService.assign_department_manager(
            self.tenant.id,
            self.dept.id,
            AssignDepartmentManagerRequest(employee_id=self.emp.id),
            user_id=self.owner.id,
        )
        with pytest.raises(ManagerAlreadyAssignedError):
            WorkforceService.assign_department_manager(
                self.tenant.id,
                self.dept.id,
                AssignDepartmentManagerRequest(employee_id=self.emp.id),
                user_id=self.owner.id,
            )

    def test_assign_department_manager_raises_if_department_not_found(self):
        with pytest.raises(DepartmentNotFoundError):
            WorkforceService.assign_department_manager(
                self.tenant.id,
                999,
                AssignDepartmentManagerRequest(employee_id=self.emp.id),
                user_id=self.owner.id,
            )

    def test_assign_department_manager_raises_if_employee_not_found(self):
        with pytest.raises(EmployeeNotFoundError):
            WorkforceService.assign_department_manager(
                self.tenant.id,
                self.dept.id,
                AssignDepartmentManagerRequest(employee_id=999),
                user_id=self.owner.id,
            )

    def test_assign_department_manager_raises_on_insufficient_permissions(self):
        member = make_user("member@example.com")
        add_member(self.tenant.id, member.id, MembershipRoles.MEMBER)
        with pytest.raises(InsufficientPermissionsError):
            WorkforceService.assign_department_manager(
                self.tenant.id,
                self.dept.id,
                AssignDepartmentManagerRequest(employee_id=self.emp.id),
                user_id=member.id,
            )

    def test_remove_department_manager_closes_assignment(self):
        assignment = WorkforceService.assign_department_manager(
            self.tenant.id,
            self.dept.id,
            AssignDepartmentManagerRequest(employee_id=self.emp.id),
            user_id=self.owner.id,
        )
        removed = WorkforceService.remove_department_manager(
            self.tenant.id,
            self.dept.id,
            assignment.id,
            RemoveDepartmentManagerRequest(reason="Stepping down"),
            user_id=self.owner.id,
        )
        assert removed.left_at is not None
        assert removed.left_reason == "Stepping down"

    def test_remove_department_manager_raises_if_not_found(self):
        with pytest.raises(ManagerAssignmentNotFoundError):
            WorkforceService.remove_department_manager(
                self.tenant.id,
                self.dept.id,
                999,
                RemoveDepartmentManagerRequest(),
                user_id=self.owner.id,
            )


class EmployeeManagerServiceTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.tenant = make_tenant(self.owner.id)
        add_member(self.tenant.id, self.owner.id, MembershipRoles.OWNER)
        dept = WorkforceService.create_department(
            self.tenant.id, DepartmentIn(name="Eng")
        )
        role = WorkforceService.create_role(self.tenant.id, RoleIn(name="Dev"))
        self.manager = WorkforceService.create_employee(
            self.tenant.id,
            EmployeeIn(
                full_name="Manager Person",
                email="manager@example.com",
                department_id=dept.id,
                role_id=role.id,
                hourly_rate="50.00",
                contract_hours_per_week=40,
                hired_at=date(2024, 1, 1),
            ),
        )
        self.emp = WorkforceService.create_employee(
            self.tenant.id,
            EmployeeIn(
                full_name="Alice Smith",
                email="alice@example.com",
                department_id=dept.id,
                role_id=role.id,
                hourly_rate="30.00",
                contract_hours_per_week=40,
                hired_at=date(2024, 3, 1),
            ),
        )

    def test_set_employee_manager(self):
        updated = WorkforceService.set_employee_manager(
            self.tenant.id,
            self.emp.id,
            SetEmployeeManagerRequest(manager_id=self.manager.id),
            user_id=self.owner.id,
        )
        assert updated.manager_id == self.manager.id

    def test_set_employee_manager_to_none_removes_manager(self):
        WorkforceService.set_employee_manager(
            self.tenant.id,
            self.emp.id,
            SetEmployeeManagerRequest(manager_id=self.manager.id),
            user_id=self.owner.id,
        )
        updated = WorkforceService.set_employee_manager(
            self.tenant.id,
            self.emp.id,
            SetEmployeeManagerRequest(manager_id=None),
            user_id=self.owner.id,
        )
        assert updated.manager_id is None

    def test_set_employee_manager_raises_if_manager_not_found(self):
        with pytest.raises(EmployeeNotFoundError):
            WorkforceService.set_employee_manager(
                self.tenant.id,
                self.emp.id,
                SetEmployeeManagerRequest(manager_id=999),
                user_id=self.owner.id,
            )

    def test_set_employee_manager_raises_if_employee_not_found(self):
        with pytest.raises(EmployeeNotFoundError):
            WorkforceService.set_employee_manager(
                self.tenant.id,
                999,
                SetEmployeeManagerRequest(manager_id=self.manager.id),
                user_id=self.owner.id,
            )

    def test_set_employee_manager_raises_on_insufficient_permissions(self):
        member = make_user("member@example.com")
        add_member(self.tenant.id, member.id, MembershipRoles.MEMBER)
        with pytest.raises(InsufficientPermissionsError):
            WorkforceService.set_employee_manager(
                self.tenant.id,
                self.emp.id,
                SetEmployeeManagerRequest(manager_id=self.manager.id),
                user_id=member.id,
            )

    def test_get_direct_reports(self):
        WorkforceService.set_employee_manager(
            self.tenant.id,
            self.emp.id,
            SetEmployeeManagerRequest(manager_id=self.manager.id),
            user_id=self.owner.id,
        )
        reports = WorkforceService.get_direct_reports(self.tenant.id, self.manager.id)
        assert len(reports) == 1
        assert reports[0].id == self.emp.id

    def test_get_direct_reports_returns_empty_when_none(self):
        reports = WorkforceService.get_direct_reports(self.tenant.id, self.manager.id)
        assert reports == []


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
