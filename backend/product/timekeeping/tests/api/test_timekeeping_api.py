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
from product.timekeeping.api import router as timekeeping_router
from product.timekeeping.dtos.dtos import (
    PeriodIn,
    RejectReportRequest,
    TimeEntryIn,
    TimeEntryUpdate,
    TimeReportIn,
)
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


class TimekeepingApiTests(TestCase):
    def _authenticate_user(self, *, email: str, full_name: str):
        auth_router.register(
            RegisterRequest(email=email, full_name=full_name, password="SecurePass123!")
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
        self.user = self._authenticate_user(
            email="owner@example.com", full_name="Owner"
        )
        self.tenant = tenants_router.create_tenant(
            TenantIn(name="Acme Corp", slug="acme"), current_user=self.user
        )
        dept = workforce_router.create_department(
            self.tenant.id, DepartmentIn(name="Engineering"), self.user
        )
        role = workforce_router.create_role(
            self.tenant.id, RoleIn(name="Developer"), self.user
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
            self.user,
        )

    def _create_period(self, name: str = "Q1 2025"):
        return timekeeping_router.create_period(
            self.tenant.id,
            PeriodIn(
                name=name, start_date=date(2025, 1, 1), end_date=date(2025, 3, 31)
            ),
            self.user,
        )

    def _create_report(self, period_id: int):
        return timekeeping_router.create_time_report(
            self.tenant.id,
            period_id,
            TimeReportIn(employee_id=self.employee.id),
            self.user,
        )

    def _add_entry(self, report_id: int):
        return timekeeping_router.create_time_entry(
            self.tenant.id,
            report_id,
            TimeEntryIn(date=date(2025, 1, 15), hours=Decimal("8")),
            self.user,
        )

    # --- Periods ---

    def test_create_period_returns_period(self):
        period = self._create_period()
        assert period.name == "Q1 2025"
        assert period.tenant_id == self.tenant.id

    def test_create_period_returns_409_on_duplicate(self):
        self._create_period()
        with pytest.raises(HTTPException) as exc:
            self._create_period()
        assert exc.value.status_code == 409

    def test_list_periods_returns_all(self):
        self._create_period("Q1 2025")
        timekeeping_router.create_period(
            self.tenant.id,
            PeriodIn(
                name="Q2 2025", start_date=date(2025, 4, 1), end_date=date(2025, 6, 30)
            ),
            self.user,
        )
        periods = timekeeping_router.list_periods(self.tenant.id, self.user, None)
        assert len(periods) == 2

    def test_get_period_returns_404_when_missing(self):
        with pytest.raises(HTTPException) as exc:
            timekeeping_router.get_period(self.tenant.id, 99999, self.user)
        assert exc.value.status_code == 404

    def test_lock_period_changes_status(self):
        period = self._create_period()
        locked = timekeeping_router.lock_period(self.tenant.id, period.id, self.user)
        assert locked.status == "locked"

    def test_lock_period_returns_409_if_already_locked(self):
        period = self._create_period()
        timekeeping_router.lock_period(self.tenant.id, period.id, self.user)
        with pytest.raises(HTTPException) as exc:
            timekeeping_router.lock_period(self.tenant.id, period.id, self.user)
        assert exc.value.status_code == 409

    # --- Time Reports ---

    def test_create_time_report_returns_report(self):
        period = self._create_period()
        report = self._create_report(period.id)
        assert report.employee_id == self.employee.id
        assert report.status == "draft"

    def test_create_time_report_returns_409_on_duplicate(self):
        period = self._create_period()
        self._create_report(period.id)
        with pytest.raises(HTTPException) as exc:
            self._create_report(period.id)
        assert exc.value.status_code == 409

    def test_list_time_reports_for_period(self):
        period = self._create_period()
        self._create_report(period.id)
        reports = timekeeping_router.list_time_reports_for_period(
            self.tenant.id, period.id, self.user
        )
        assert len(reports) == 1

    def test_get_time_report_returns_404_when_missing(self):
        with pytest.raises(HTTPException) as exc:
            timekeeping_router.get_time_report(self.tenant.id, 99999, self.user)
        assert exc.value.status_code == 404

    def test_submit_time_report_changes_status(self):
        period = self._create_period()
        report = self._create_report(period.id)
        self._add_entry(report.id)
        submitted = timekeeping_router.submit_time_report(
            self.tenant.id, report.id, self.user
        )
        assert submitted.status == "submitted"

    def test_submit_time_report_returns_422_without_entries(self):
        period = self._create_period()
        report = self._create_report(period.id)
        with pytest.raises(HTTPException) as exc:
            timekeeping_router.submit_time_report(self.tenant.id, report.id, self.user)
        assert exc.value.status_code == 422

    def test_approve_time_report(self):
        period = self._create_period()
        report = self._create_report(period.id)
        self._add_entry(report.id)
        timekeeping_router.submit_time_report(self.tenant.id, report.id, self.user)
        approved = timekeeping_router.approve_time_report(
            self.tenant.id, report.id, self.user
        )
        assert approved.status == "approved"

    def test_reject_time_report(self):
        period = self._create_period()
        report = self._create_report(period.id)
        self._add_entry(report.id)
        timekeeping_router.submit_time_report(self.tenant.id, report.id, self.user)
        rejected = timekeeping_router.reject_time_report(
            self.tenant.id,
            report.id,
            RejectReportRequest(reason="Needs review"),
            self.user,
        )
        assert rejected.status == "rejected"
        assert rejected.rejection_reason == "Needs review"

    def test_list_report_history(self):
        period = self._create_period()
        report = self._create_report(period.id)
        self._add_entry(report.id)
        timekeeping_router.submit_time_report(self.tenant.id, report.id, self.user)
        history = timekeeping_router.list_report_history(
            self.tenant.id, report.id, self.user
        )
        assert len(history) == 1
        assert history[0].to_status == "submitted"

    # --- Time Entries ---

    def test_create_time_entry_returns_entry(self):
        period = self._create_period()
        report = self._create_report(period.id)
        entry = self._add_entry(report.id)
        assert entry.report_id == report.id
        assert entry.hours == Decimal("8")

    def test_list_time_entries(self):
        period = self._create_period()
        report = self._create_report(period.id)
        self._add_entry(report.id)
        timekeeping_router.create_time_entry(
            self.tenant.id,
            report.id,
            TimeEntryIn(date=date(2025, 1, 16), hours=Decimal("6")),
            self.user,
        )
        entries = timekeeping_router.list_time_entries(
            self.tenant.id, report.id, self.user
        )
        assert len(entries) == 2

    def test_update_time_entry(self):
        period = self._create_period()
        report = self._create_report(period.id)
        entry = self._add_entry(report.id)
        updated = timekeeping_router.update_time_entry(
            self.tenant.id,
            report.id,
            entry.id,
            TimeEntryUpdate(date=date(2025, 1, 15), hours=Decimal("4")),
            self.user,
        )
        assert updated.hours == Decimal("4")

    def test_delete_time_entry(self):
        period = self._create_period()
        report = self._create_report(period.id)
        entry = self._add_entry(report.id)
        timekeeping_router.delete_time_entry(
            self.tenant.id, report.id, entry.id, self.user
        )
        entries = timekeeping_router.list_time_entries(
            self.tenant.id, report.id, self.user
        )
        assert len(entries) == 0

    def test_create_time_entry_returns_422_on_submitted_report(self):
        period = self._create_period()
        report = self._create_report(period.id)
        self._add_entry(report.id)
        timekeeping_router.submit_time_report(self.tenant.id, report.id, self.user)
        with pytest.raises(HTTPException) as exc:
            timekeeping_router.create_time_entry(
                self.tenant.id,
                report.id,
                TimeEntryIn(date=date(2025, 1, 16), hours=Decimal("8")),
                self.user,
            )
        assert exc.value.status_code == 422
