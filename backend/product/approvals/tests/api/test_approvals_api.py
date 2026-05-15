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
from infra.tenants.dtos.dtos import AddMemberRequest, TenantIn
from product.approvals.api import router as approvals_router
from product.approvals.dtos.dtos import RejectApprovalIn
from product.timekeeping.api import router as timekeeping_router
from product.timekeeping.dtos.dtos import PeriodIn, TimeEntryIn, TimeReportIn
from product.workforce.api import router as workforce_router
from product.workforce.dtos.dtos import DepartmentIn, EmployeeIn, RoleIn


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


class ApprovalsApiTests(TestCase):
    def _authenticate(self, *, email: str, full_name: str):
        auth_router.register(
            RegisterRequest(
                email=email, full_name=full_name, password="SecurePass123!"
            ),
            build_request(),
        )
        login_response = auth_router.login_user(
            LoginRequest(email=email, password="SecurePass123!"),
            build_request(),
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=login_response.access_token
        )
        return get_current_user(credentials)

    def setUp(self):
        self.manager = self._authenticate(email="mgr@example.com", full_name="Manager")
        self.employee_user = self._authenticate(
            email="emp@example.com", full_name="Employee"
        )

        self.tenant = tenants_router.create(
            TenantIn(name="Acme Corp", slug="acme"), current_user=self.manager
        )
        tenants_router.add_member(
            self.tenant.id,
            AddMemberRequest(user_id=self.employee_user.id, role="employee"),
            current_user=self.manager,
        )

        dept = workforce_router.create_department(
            self.tenant.id, DepartmentIn(name="Engineering"), self.manager
        )
        role = workforce_router.create_role(
            self.tenant.id, RoleIn(name="Developer"), self.manager
        )
        self.employee = workforce_router.create_employee(
            self.tenant.id,
            EmployeeIn(
                full_name="Alice Smith",
                email="alice@example.com",
                department_id=dept.id,
                role_id=role.id,
                hourly_rate=Decimal("30.00"),
                contract_hours_per_week=40,
                hired_at=date(2024, 1, 1),
            ),
            self.manager,
        )

        self.period = timekeeping_router.create_period(
            self.tenant.id,
            PeriodIn(
                name="April 2025",
                start_date=date(2025, 4, 1),
                end_date=date(2025, 4, 30),
            ),
            self.manager,
        )
        self.report = timekeeping_router.create_time_report(
            self.tenant.id,
            self.period.id,
            TimeReportIn(employee_id=self.employee.id),
            self.employee_user,
        )
        timekeeping_router.create_time_entry(
            self.tenant.id,
            self.report.id,
            TimeEntryIn(date=date(2025, 4, 1), hours=Decimal("8")),
            self.employee_user,
        )

    def _submit(self):
        return approvals_router.submit_report_for_approval(
            self.tenant.id, self.report.id, current_user=self.employee_user
        )

    def test_submit_creates_approval_with_pending_status(self):
        approval = self._submit()

        assert approval.tenant_id == self.tenant.id
        assert approval.report_id == self.report.id
        assert approval.status == "pending"

    def test_submit_returns_409_if_already_submitted(self):
        self._submit()

        with pytest.raises(HTTPException) as exc:
            self._submit()

        assert exc.value.status_code == 409

    def test_approve_sets_status_to_approved(self):
        approval = self._submit()

        updated = approvals_router.approve_report(
            self.tenant.id, approval.id, current_user=self.manager
        )

        assert updated.status == "approved"
        assert updated.reviewer_id == self.manager.id

    def test_approve_returns_403_for_non_manager(self):
        approval = self._submit()

        with pytest.raises(HTTPException) as exc:
            approvals_router.approve_report(
                self.tenant.id, approval.id, current_user=self.employee_user
            )

        assert exc.value.status_code == 403

    def test_approve_returns_409_if_already_approved(self):
        approval = self._submit()
        approvals_router.approve_report(
            self.tenant.id, approval.id, current_user=self.manager
        )

        with pytest.raises(HTTPException) as exc:
            approvals_router.approve_report(
                self.tenant.id, approval.id, current_user=self.manager
            )

        assert exc.value.status_code == 409

    def test_reject_sets_status_to_rejected_with_reason(self):
        approval = self._submit()

        updated = approvals_router.reject_report(
            self.tenant.id,
            approval.id,
            RejectApprovalIn(reason="Missing Thursday"),
            current_user=self.manager,
        )

        assert updated.status == "rejected"
        assert updated.reviewer_id == self.manager.id

    def test_reject_returns_403_for_non_manager(self):
        approval = self._submit()

        with pytest.raises(HTTPException) as exc:
            approvals_router.reject_report(
                self.tenant.id,
                approval.id,
                RejectApprovalIn(reason="Bad data"),
                current_user=self.employee_user,
            )

        assert exc.value.status_code == 403

    def test_list_approvals_returns_all_for_tenant(self):
        self._submit()

        approvals = approvals_router.list_approvals(
            self.tenant.id, current_user=self.manager
        )

        assert len(approvals) == 1
        assert approvals[0].tenant_id == self.tenant.id

    def test_list_approvals_filters_by_status(self):
        approval = self._submit()
        approvals_router.approve_report(
            self.tenant.id, approval.id, current_user=self.manager
        )

        pending = approvals_router.list_approvals(
            self.tenant.id, current_user=self.manager, status="pending"
        )
        approved = approvals_router.list_approvals(
            self.tenant.id, current_user=self.manager, status="approved"
        )

        assert len(pending) == 0
        assert len(approved) == 1

    def test_get_approval_returns_correct_record(self):
        approval = self._submit()

        found = approvals_router.get_approval(
            self.tenant.id, approval.id, current_user=self.employee_user
        )

        assert found.id == approval.id

    def test_get_approval_returns_404_if_not_found(self):
        with pytest.raises(HTTPException) as exc:
            approvals_router.get_approval(
                self.tenant.id, 99999, current_user=self.manager
            )

        assert exc.value.status_code == 404

    def test_get_approval_returns_404_for_other_tenant(self):
        approval = self._submit()

        other_manager = self._authenticate(email="other@example.com", full_name="Other")
        other_tenant = tenants_router.create(
            TenantIn(name="Other Corp", slug="other"), current_user=other_manager
        )

        with pytest.raises(HTTPException) as exc:
            approvals_router.get_approval(
                other_tenant.id, approval.id, current_user=other_manager
            )

        assert exc.value.status_code == 404

    def test_list_events_returns_full_trail(self):
        approval = self._submit()
        approvals_router.approve_report(
            self.tenant.id, approval.id, current_user=self.manager
        )

        events = approvals_router.list_approval_events(
            self.tenant.id, approval.id, current_user=self.manager
        )

        assert len(events) == 2
        assert events[0].action == "submitted"
        assert events[1].action == "approved"

    def test_endpoints_require_authentication(self):
        with pytest.raises(HTTPException) as exc:
            get_current_user(None)

        assert exc.value.status_code == 401
