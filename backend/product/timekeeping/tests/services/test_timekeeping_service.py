from datetime import date, time
from decimal import Decimal

import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.common.exceptions import Conflict, Forbidden, NotFound, UnprocessableEntity
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.services.tenants_service import TenantService
from product.common.classes import PeriodStatus, TimeReportStatus
from product.timekeeping.dtos.dtos import (
    PeriodIn,
    RejectReportRequest,
    TimeEntryIn,
    TimeEntryUpdate,
    TimeReportIn,
)
from product.workforce.dtos.dtos import DepartmentIn, EmployeeIn, RoleIn
from product.workforce.services.workforce_service import WorkforceService

from product.timekeeping.services.timekeeping_service import TimekeepingService


def make_user(email: str = "owner@example.com"):
    return AuthRepository.create_user(
        email=email,
        full_name="Test User",
        password_hash=AuthService._hash_password("SecurePass123!"),
    )


def make_tenant(user_id: int, slug: str = "acme"):
    return TenantService.create(TenantEntity(name="Acme Corp", slug=slug), created_by_id=user_id)


def add_member(tenant_id: int, user_id: int, role: MembershipRoles):
    TenantService.add_membership(
        tenant_id=tenant_id,
        user_id=user_id,
        entity=TenantMembershipEntity(role=role.value),
        invited_by_id=None,
    )


def make_employee(tenant_id: int, email: str = "emp@example.com"):
    dept = WorkforceService.create_department(tenant_id, DepartmentIn(name=f"Dept-{email}"))
    role = WorkforceService.create_role(tenant_id, RoleIn(name=f"Role-{email}"))
    return WorkforceService.create_employee(
        tenant_id,
        EmployeeIn(
            full_name="Test Employee",
            email=email,
            department_id=dept.id,
            role_id=role.id,
            hourly_rate=Decimal("25.00"),
            contract_hours_per_week=40,
            hired_at=date(2024, 1, 1),
        ),
    )


class PeriodServiceTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        add_member(self.tenant.id, self.user.id, MembershipRoles.OWNER)

    def _period(self, name: str = "Q1 2025", **kwargs):
        defaults = dict(name=name, start_date=date(2025, 1, 1), end_date=date(2025, 3, 31))
        return PeriodIn(**{**defaults, **kwargs})

    def test_create_period_normalizes_name(self):
        period = TimekeepingService.create_period(
            self.tenant.id, self._period(name="  Q1 2025  "), self.user.id
        )
        assert period.name == "Q1 2025"
        assert period.tenant_id == self.tenant.id
        assert period.status == PeriodStatus.OPEN

    def test_create_period_raises_on_duplicate_name(self):
        TimekeepingService.create_period(self.tenant.id, self._period(), self.user.id)
        with pytest.raises(Conflict, match="Q1 2025"):
            TimekeepingService.create_period(self.tenant.id, self._period(), self.user.id)

    def test_create_period_raises_on_overlapping_dates(self):
        TimekeepingService.create_period(self.tenant.id, self._period("Q1"), self.user.id)
        with pytest.raises(Conflict, match="overlaps"):
            TimekeepingService.create_period(
                self.tenant.id,
                self._period("Q1-partial", start_date=date(2025, 2, 1), end_date=date(2025, 4, 30)),
                self.user.id,
            )

    def test_create_period_raises_on_insufficient_permissions(self):
        employee = make_user("emp@example.com")
        add_member(self.tenant.id, employee.id, MembershipRoles.EMPLOYEE)
        with pytest.raises(Forbidden):
            TimekeepingService.create_period(self.tenant.id, self._period(), employee.id)

    def test_get_period_returns_period(self):
        created = TimekeepingService.create_period(self.tenant.id, self._period(), self.user.id)
        found = TimekeepingService.get_period(self.tenant.id, created.id, self.user.id)
        assert found.id == created.id

    def test_get_period_raises_if_not_found(self):
        with pytest.raises(NotFound):
            TimekeepingService.get_period(self.tenant.id, 99999, self.user.id)

    def test_get_period_raises_if_belongs_to_other_tenant(self):
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, slug="other")
        add_member(other_tenant.id, other_user.id, MembershipRoles.OWNER)
        period = TimekeepingService.create_period(other_tenant.id, self._period(), other_user.id)
        with pytest.raises(NotFound):
            TimekeepingService.get_period(self.tenant.id, period.id, self.user.id)

    def test_list_periods_returns_all_for_tenant(self):
        TimekeepingService.create_period(
            self.tenant.id,
            PeriodIn(name="Q1", start_date=date(2025, 1, 1), end_date=date(2025, 3, 31)),
            self.user.id,
        )
        TimekeepingService.create_period(
            self.tenant.id,
            PeriodIn(name="Q2", start_date=date(2025, 4, 1), end_date=date(2025, 6, 30)),
            self.user.id,
        )
        periods = TimekeepingService.list_periods(self.tenant.id, self.user.id)
        assert len(periods) == 2

    def test_list_periods_filters_by_status(self):
        period = TimekeepingService.create_period(self.tenant.id, self._period(), self.user.id)
        TimekeepingService.lock_period(self.tenant.id, period.id, self.user.id)

        open_periods = TimekeepingService.list_periods(
            self.tenant.id, self.user.id, status=PeriodStatus.OPEN
        )
        locked_periods = TimekeepingService.list_periods(
            self.tenant.id, self.user.id, status=PeriodStatus.LOCKED
        )

        assert len(open_periods) == 0
        assert len(locked_periods) == 1

    def test_lock_period_changes_status_to_locked(self):
        period = TimekeepingService.create_period(self.tenant.id, self._period(), self.user.id)
        locked = TimekeepingService.lock_period(self.tenant.id, period.id, self.user.id)
        assert locked.status == PeriodStatus.LOCKED
        assert locked.locked_at is not None
        assert locked.locked_by_id == self.user.id

    def test_lock_period_raises_if_already_locked(self):
        period = TimekeepingService.create_period(self.tenant.id, self._period(), self.user.id)
        TimekeepingService.lock_period(self.tenant.id, period.id, self.user.id)
        with pytest.raises(Conflict, match="already locked"):
            TimekeepingService.lock_period(self.tenant.id, period.id, self.user.id)

    def test_lock_period_raises_if_not_found(self):
        with pytest.raises(NotFound):
            TimekeepingService.lock_period(self.tenant.id, 99999, self.user.id)


class TimeReportServiceTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        add_member(self.tenant.id, self.user.id, MembershipRoles.OWNER)
        self.employee = make_employee(self.tenant.id)
        self.period = TimekeepingService.create_period(
            self.tenant.id,
            PeriodIn(name="Q1", start_date=date(2025, 1, 1), end_date=date(2025, 3, 31)),
            self.user.id,
        )

    def _add_entry(self, report_id: int):
        return TimekeepingService.create_time_entry(
            self.tenant.id,
            report_id,
            TimeEntryIn(date=date(2025, 1, 15), hours=Decimal("8")),
            self.user.id,
        )

    def test_create_time_report(self):
        report = TimekeepingService.create_time_report(
            self.tenant.id, self.period.id, TimeReportIn(employee_id=self.employee.id), self.user.id
        )
        assert report.employee_id == self.employee.id
        assert report.period_id == self.period.id
        assert report.status == TimeReportStatus.DRAFT

    def test_create_time_report_raises_on_locked_period(self):
        TimekeepingService.lock_period(self.tenant.id, self.period.id, self.user.id)
        with pytest.raises(Conflict, match="locked"):
            TimekeepingService.create_time_report(
                self.tenant.id,
                self.period.id,
                TimeReportIn(employee_id=self.employee.id),
                self.user.id,
            )

    def test_create_time_report_raises_on_duplicate(self):
        TimekeepingService.create_time_report(
            self.tenant.id, self.period.id, TimeReportIn(employee_id=self.employee.id), self.user.id
        )
        with pytest.raises(Conflict):
            TimekeepingService.create_time_report(
                self.tenant.id,
                self.period.id,
                TimeReportIn(employee_id=self.employee.id),
                self.user.id,
            )

    def test_get_time_report_returns_report(self):
        report = TimekeepingService.create_time_report(
            self.tenant.id, self.period.id, TimeReportIn(employee_id=self.employee.id), self.user.id
        )
        found = TimekeepingService.get_time_report(self.tenant.id, report.id, self.user.id)
        assert found.id == report.id

    def test_get_time_report_raises_if_not_found(self):
        with pytest.raises(NotFound):
            TimekeepingService.get_time_report(self.tenant.id, 99999, self.user.id)

    def test_list_time_reports_for_period(self):
        emp2 = make_employee(self.tenant.id, "emp2@example.com")
        TimekeepingService.create_time_report(
            self.tenant.id, self.period.id, TimeReportIn(employee_id=self.employee.id), self.user.id
        )
        TimekeepingService.create_time_report(
            self.tenant.id, self.period.id, TimeReportIn(employee_id=emp2.id), self.user.id
        )
        reports = TimekeepingService.list_time_reports(
            self.tenant.id, self.user.id, period_id=self.period.id
        )
        assert len(reports) == 2

    def test_submit_time_report_requires_entries(self):
        report = TimekeepingService.create_time_report(
            self.tenant.id, self.period.id, TimeReportIn(employee_id=self.employee.id), self.user.id
        )
        with pytest.raises(UnprocessableEntity, match="empty"):
            TimekeepingService.submit_time_report(self.tenant.id, report.id, self.user.id)

    def test_submit_time_report_changes_status(self):
        report = TimekeepingService.create_time_report(
            self.tenant.id, self.period.id, TimeReportIn(employee_id=self.employee.id), self.user.id
        )
        self._add_entry(report.id)
        submitted = TimekeepingService.submit_time_report(self.tenant.id, report.id, self.user.id)
        assert submitted.status == TimeReportStatus.SUBMITTED
        assert submitted.submitted_at is not None

    def test_submit_time_report_raises_if_already_submitted(self):
        report = TimekeepingService.create_time_report(
            self.tenant.id, self.period.id, TimeReportIn(employee_id=self.employee.id), self.user.id
        )
        self._add_entry(report.id)
        TimekeepingService.submit_time_report(self.tenant.id, report.id, self.user.id)
        with pytest.raises(Conflict, match="status"):
            TimekeepingService.submit_time_report(self.tenant.id, report.id, self.user.id)

    def test_approve_time_report(self):
        report = TimekeepingService.create_time_report(
            self.tenant.id, self.period.id, TimeReportIn(employee_id=self.employee.id), self.user.id
        )
        self._add_entry(report.id)
        TimekeepingService.submit_time_report(self.tenant.id, report.id, self.user.id)
        approved = TimekeepingService.approve_time_report(self.tenant.id, report.id, self.user.id)
        assert approved.status == TimeReportStatus.APPROVED
        assert approved.approved_at is not None

    def test_approve_time_report_raises_if_not_submitted(self):
        report = TimekeepingService.create_time_report(
            self.tenant.id, self.period.id, TimeReportIn(employee_id=self.employee.id), self.user.id
        )
        with pytest.raises(Conflict, match="status"):
            TimekeepingService.approve_time_report(self.tenant.id, report.id, self.user.id)

    def test_approve_time_report_raises_on_insufficient_permissions(self):
        employee_user = make_user("employee@example.com")
        add_member(self.tenant.id, employee_user.id, MembershipRoles.EMPLOYEE)
        report = TimekeepingService.create_time_report(
            self.tenant.id, self.period.id, TimeReportIn(employee_id=self.employee.id), self.user.id
        )
        self._add_entry(report.id)
        TimekeepingService.submit_time_report(self.tenant.id, report.id, self.user.id)
        with pytest.raises(Forbidden):
            TimekeepingService.approve_time_report(self.tenant.id, report.id, employee_user.id)

    def test_reject_time_report(self):
        report = TimekeepingService.create_time_report(
            self.tenant.id, self.period.id, TimeReportIn(employee_id=self.employee.id), self.user.id
        )
        self._add_entry(report.id)
        TimekeepingService.submit_time_report(self.tenant.id, report.id, self.user.id)
        rejected = TimekeepingService.reject_time_report(
            self.tenant.id,
            report.id,
            RejectReportRequest(reason="Missing hours"),
            self.user.id,
        )
        assert rejected.status == TimeReportStatus.REJECTED
        assert rejected.rejection_reason == "Missing hours"
        assert rejected.rejected_at is not None

    def test_reject_time_report_raises_if_not_submitted(self):
        report = TimekeepingService.create_time_report(
            self.tenant.id, self.period.id, TimeReportIn(employee_id=self.employee.id), self.user.id
        )
        with pytest.raises(Conflict, match="status"):
            TimekeepingService.reject_time_report(
                self.tenant.id, report.id, RejectReportRequest(), self.user.id
            )

    def test_submit_creates_status_history_entry(self):
        report = TimekeepingService.create_time_report(
            self.tenant.id, self.period.id, TimeReportIn(employee_id=self.employee.id), self.user.id
        )
        self._add_entry(report.id)
        TimekeepingService.submit_time_report(self.tenant.id, report.id, self.user.id)
        history = TimekeepingService.list_report_history(self.tenant.id, report.id, self.user.id)
        assert len(history) == 1
        assert history[0].from_status == TimeReportStatus.DRAFT
        assert history[0].to_status == TimeReportStatus.SUBMITTED

    def test_approve_creates_status_history_entry(self):
        report = TimekeepingService.create_time_report(
            self.tenant.id, self.period.id, TimeReportIn(employee_id=self.employee.id), self.user.id
        )
        self._add_entry(report.id)
        TimekeepingService.submit_time_report(self.tenant.id, report.id, self.user.id)
        TimekeepingService.approve_time_report(self.tenant.id, report.id, self.user.id)
        history = TimekeepingService.list_report_history(self.tenant.id, report.id, self.user.id)
        assert len(history) == 2
        assert history[-1].to_status == TimeReportStatus.APPROVED


class TimeEntryServiceTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        add_member(self.tenant.id, self.user.id, MembershipRoles.OWNER)
        self.employee = make_employee(self.tenant.id)
        period = TimekeepingService.create_period(
            self.tenant.id,
            PeriodIn(name="Q1", start_date=date(2025, 1, 1), end_date=date(2025, 3, 31)),
            self.user.id,
        )
        self.report = TimekeepingService.create_time_report(
            self.tenant.id,
            period.id,
            TimeReportIn(employee_id=self.employee.id),
            self.user.id,
        )

    def test_create_time_entry(self):
        entry = TimekeepingService.create_time_entry(
            self.tenant.id,
            self.report.id,
            TimeEntryIn(date=date(2025, 1, 15), hours=Decimal("8")),
            self.user.id,
        )
        assert entry.report_id == self.report.id
        assert entry.hours == Decimal("8")
        assert entry.date == date(2025, 1, 15)

    def test_create_time_entry_raises_if_report_not_draft(self):
        TimekeepingService.create_time_entry(
            self.tenant.id,
            self.report.id,
            TimeEntryIn(date=date(2025, 1, 15), hours=Decimal("8")),
            self.user.id,
        )
        TimekeepingService.submit_time_report(self.tenant.id, self.report.id, self.user.id)
        with pytest.raises(UnprocessableEntity, match="status"):
            TimekeepingService.create_time_entry(
                self.tenant.id,
                self.report.id,
                TimeEntryIn(date=date(2025, 1, 16), hours=Decimal("8")),
                self.user.id,
            )

    def test_list_time_entries(self):
        TimekeepingService.create_time_entry(
            self.tenant.id,
            self.report.id,
            TimeEntryIn(date=date(2025, 1, 15), hours=Decimal("8")),
            self.user.id,
        )
        TimekeepingService.create_time_entry(
            self.tenant.id,
            self.report.id,
            TimeEntryIn(date=date(2025, 1, 16), hours=Decimal("6")),
            self.user.id,
        )
        entries = TimekeepingService.list_time_entries(self.tenant.id, self.report.id, self.user.id)
        assert len(entries) == 2

    def test_update_time_entry_changes_hours(self):
        entry = TimekeepingService.create_time_entry(
            self.tenant.id,
            self.report.id,
            TimeEntryIn(date=date(2025, 1, 15), hours=Decimal("8")),
            self.user.id,
        )
        updated = TimekeepingService.update_time_entry(
            self.tenant.id,
            self.report.id,
            entry.id,
            TimeEntryUpdate(hours=Decimal("6")),
            self.user.id,
        )
        assert updated.hours == Decimal("6")

    def test_update_time_entry_creates_change_history(self):
        from product.timekeeping.repositories.timekeeping_repository import TimekeepingRepository

        entry = TimekeepingService.create_time_entry(
            self.tenant.id,
            self.report.id,
            TimeEntryIn(date=date(2025, 1, 15), hours=Decimal("8")),
            self.user.id,
        )
        TimekeepingService.update_time_entry(
            self.tenant.id,
            self.report.id,
            entry.id,
            TimeEntryUpdate(hours=Decimal("6")),
            self.user.id,
        )
        history = TimekeepingRepository.list_entry_change_history(entry.id)
        assert len(history) == 1
        assert history[0].field_name == "hours"
        assert history[0].old_value == "8.00"
        assert history[0].new_value == "6"

    def test_update_time_entry_raises_if_report_not_draft(self):
        entry = TimekeepingService.create_time_entry(
            self.tenant.id,
            self.report.id,
            TimeEntryIn(date=date(2025, 1, 15), hours=Decimal("8")),
            self.user.id,
        )
        TimekeepingService.submit_time_report(self.tenant.id, self.report.id, self.user.id)
        with pytest.raises(UnprocessableEntity, match="status"):
            TimekeepingService.update_time_entry(
                self.tenant.id,
                self.report.id,
                entry.id,
                TimeEntryUpdate(hours=Decimal("6")),
                self.user.id,
            )

    def test_delete_time_entry(self):
        entry = TimekeepingService.create_time_entry(
            self.tenant.id,
            self.report.id,
            TimeEntryIn(date=date(2025, 1, 15), hours=Decimal("8")),
            self.user.id,
        )
        TimekeepingService.delete_time_entry(
            self.tenant.id, self.report.id, entry.id, self.user.id
        )
        entries = TimekeepingService.list_time_entries(self.tenant.id, self.report.id, self.user.id)
        assert len(entries) == 0

    def test_delete_time_entry_raises_if_report_not_draft(self):
        entry = TimekeepingService.create_time_entry(
            self.tenant.id,
            self.report.id,
            TimeEntryIn(date=date(2025, 1, 15), hours=Decimal("8")),
            self.user.id,
        )
        TimekeepingService.submit_time_report(self.tenant.id, self.report.id, self.user.id)
        with pytest.raises(UnprocessableEntity, match="status"):
            TimekeepingService.delete_time_entry(
                self.tenant.id, self.report.id, entry.id, self.user.id
            )

    def test_delete_time_entry_raises_if_not_found(self):
        with pytest.raises(NotFound):
            TimekeepingService.delete_time_entry(
                self.tenant.id, self.report.id, 99999, self.user.id
            )
