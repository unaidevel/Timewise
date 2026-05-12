import contextlib
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.common.exceptions import Conflict, InternalServerError, NotFound
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.services.tenants_service import TenantService
from product.common.classes import TimeReportStatus
from product.timekeeping.dtos.dtos import (
    PeriodIn,
    RejectReportRequest,
    TimeEntryIn,
    TimeEntryUpdate,
    TimeReportIn,
)
from product.timekeeping.orchestrators.timekeeping_orchestrator import (
    TimekeepingOrchestrator,
)
from product.timekeeping.repositories.timekeeping_repository import (
    TimekeepingRepository,
)
from product.workforce.dtos.dtos import DepartmentIn, EmployeeIn, RoleIn
from product.workforce.services.workforce_service import WorkforceService
from shared.audit.repositories.audit_repository import AuditRepository


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


def make_employee(tenant_id: int, email: str = "emp@example.com"):
    dept = WorkforceService.create_department(
        tenant_id, DepartmentIn(name=f"Dept-{email}")
    )
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


def latest_audit(tenant_id: int):
    events = AuditRepository.get_all(tenant_id)
    assert events, "expected at least one audit event"
    return events[0]


class TimekeepingOrchestratorAuditTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        add_member(self.tenant.id, self.user.id, MembershipRoles.OWNER)
        self.employee = make_employee(self.tenant.id)

    def _period(self, name: str = "Q1 2025"):
        return PeriodIn(
            name=name, start_date=date(2025, 1, 1), end_date=date(2025, 3, 31)
        )

    def _create_period_with_audit(self) -> int:
        period = TimekeepingOrchestrator.create_period(
            self.tenant.id, self._period(), self.user.id
        )
        return period.id

    def _create_report(self, period_id: int):
        return TimekeepingOrchestrator.create_time_report(
            self.tenant.id,
            period_id,
            TimeReportIn(employee_id=self.employee.id),
            self.user.id,
        )

    def _add_entry(self, report_id: int):
        return TimekeepingOrchestrator.create_time_entry(
            self.tenant.id,
            report_id,
            TimeEntryIn(date=date(2025, 1, 15), hours=Decimal("8")),
            self.user.id,
        )

    def test_create_period_emits_audit_event(self):
        period = TimekeepingOrchestrator.create_period(
            self.tenant.id, self._period(), self.user.id
        )

        event = latest_audit(self.tenant.id)
        assert event.action == "period.created"
        assert event.resource_type == "Period"
        assert event.resource_id == period.id
        assert event.actor_id == self.user.id
        assert event.metadata["name"] == period.name

    def test_lock_period_emits_audit_event(self):
        period_id = self._create_period_with_audit()
        AuditRepository.delete(latest_audit(self.tenant.id).id)

        TimekeepingOrchestrator.lock_period(self.tenant.id, period_id, self.user.id)

        event = latest_audit(self.tenant.id)
        assert event.action == "period.locked"
        assert event.resource_id == period_id

    def test_create_time_report_emits_audit_event(self):
        period_id = self._create_period_with_audit()

        report = self._create_report(period_id)

        event = latest_audit(self.tenant.id)
        assert event.action == "time_report.created"
        assert event.resource_type == "TimeReport"
        assert event.resource_id == report.id
        assert event.metadata["period_id"] == period_id
        assert event.metadata["employee_id"] == self.employee.id

    def test_create_time_entry_emits_audit_event(self):
        period_id = self._create_period_with_audit()
        report = self._create_report(period_id)

        entry = self._add_entry(report.id)

        event = latest_audit(self.tenant.id)
        assert event.action == "time_entry.created"
        assert event.resource_type == "TimeEntry"
        assert event.resource_id == entry.id
        assert event.metadata["report_id"] == report.id
        assert event.metadata["hours"] == "8"

    def test_update_time_entry_emits_audit_event(self):
        period_id = self._create_period_with_audit()
        report = self._create_report(period_id)
        entry = self._add_entry(report.id)

        TimekeepingOrchestrator.update_time_entry(
            self.tenant.id,
            report.id,
            entry.id,
            TimeEntryUpdate(date=date(2025, 1, 15), hours=Decimal("6")),
            self.user.id,
        )

        event = latest_audit(self.tenant.id)
        assert event.action == "time_entry.updated"
        assert event.resource_id == entry.id
        assert event.metadata["hours"] == "6.00"

    def test_delete_time_entry_emits_audit_event(self):
        period_id = self._create_period_with_audit()
        report = self._create_report(period_id)
        entry = self._add_entry(report.id)

        TimekeepingOrchestrator.delete_time_entry(
            self.tenant.id, report.id, entry.id, self.user.id
        )

        event = latest_audit(self.tenant.id)
        assert event.action == "time_entry.deleted"
        assert event.resource_id == entry.id
        assert event.metadata["report_id"] == report.id

    def test_submit_time_report_emits_audit_event_with_status_transition(self):
        period_id = self._create_period_with_audit()
        report = self._create_report(period_id)
        self._add_entry(report.id)

        TimekeepingOrchestrator.submit_time_report(
            self.tenant.id, report.id, self.user.id
        )

        event = latest_audit(self.tenant.id)
        assert event.action == "time_report.submitted"
        assert event.outcome == "success"
        assert event.resource_id == report.id
        assert event.metadata["to_status"] == TimeReportStatus.SUBMITTED

    def test_approve_time_report_emits_audit_event(self):
        period_id = self._create_period_with_audit()
        report = self._create_report(period_id)
        self._add_entry(report.id)
        TimekeepingOrchestrator.submit_time_report(
            self.tenant.id, report.id, self.user.id
        )

        TimekeepingOrchestrator.approve_time_report(
            self.tenant.id, report.id, self.user.id
        )

        event = latest_audit(self.tenant.id)
        assert event.action == "time_report.approved"
        assert event.resource_id == report.id
        assert event.metadata["to_status"] == TimeReportStatus.APPROVED

    def test_reject_time_report_emits_audit_event_with_reason(self):
        period_id = self._create_period_with_audit()
        report = self._create_report(period_id)
        self._add_entry(report.id)
        TimekeepingOrchestrator.submit_time_report(
            self.tenant.id, report.id, self.user.id
        )

        TimekeepingOrchestrator.reject_time_report(
            self.tenant.id,
            report.id,
            RejectReportRequest(reason="missing details"),
            self.user.id,
        )

        event = latest_audit(self.tenant.id)
        assert event.action == "time_report.rejected"
        assert event.resource_id == report.id
        assert event.metadata["reason"] == "missing details"
        assert event.metadata["to_status"] == TimeReportStatus.REJECTED


class TimekeepingOrchestratorTransactionalityTests(TestCase):
    """Verify that business write + audit write are atomic."""

    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        add_member(self.tenant.id, self.user.id, MembershipRoles.OWNER)
        self.employee = make_employee(self.tenant.id)

    def test_audit_failure_rolls_back_business_write(self):
        with (
            patch(
                "shared.audit.services.audit_service.AuditRepository.create",
                side_effect=InternalServerError("audit boom"),
            ),
            contextlib.suppress(InternalServerError),
        ):
            TimekeepingOrchestrator.create_period(
                self.tenant.id,
                PeriodIn(
                    name="Boom",
                    start_date=date(2025, 1, 1),
                    end_date=date(2025, 3, 31),
                ),
                self.user.id,
            )

        # business write must have rolled back
        assert TimekeepingRepository.find_period_by_name(self.tenant.id, "Boom") is None


class TimekeepingOrchestratorFailureAuditTests(TestCase):
    """A failed business operation must produce a failure audit row,
    while still rolling back the business write."""

    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        add_member(self.tenant.id, self.user.id, MembershipRoles.OWNER)
        self.employee = make_employee(self.tenant.id)

    def _period(self, name: str = "Q1 2025"):
        return PeriodIn(
            name=name, start_date=date(2025, 1, 1), end_date=date(2025, 3, 31)
        )

    def test_duplicate_period_records_failure_audit_and_rolls_back(self):
        # First create succeeds (and audits success).
        TimekeepingOrchestrator.create_period(
            self.tenant.id, self._period(), self.user.id
        )

        # Second create must raise Conflict.
        try:
            TimekeepingOrchestrator.create_period(
                self.tenant.id, self._period(), self.user.id
            )
            raise AssertionError("expected Conflict")
        except Conflict:
            pass

        # Exactly one period persisted (the first one).
        periods = TimekeepingRepository.list_periods(self.tenant.id)
        assert len(periods) == 1

        # And we have a failure audit row.
        events = AuditRepository.get_all(
            self.tenant.id, "period.created", None, None, None, "failure"
        )
        assert len(events) == 1
        failure_event = events[0]
        assert failure_event.outcome == "failure"
        assert failure_event.action == "period.created"
        assert failure_event.metadata["error_type"] == "Conflict"
        assert "Q1 2025" in failure_event.metadata["error_message"]
        assert failure_event.metadata["name"] == "Q1 2025"

    def test_submit_in_wrong_status_records_failure_audit(self):
        period = TimekeepingOrchestrator.create_period(
            self.tenant.id, self._period(), self.user.id
        )
        report = TimekeepingOrchestrator.create_time_report(
            self.tenant.id,
            period.id,
            TimeReportIn(employee_id=self.employee.id),
            self.user.id,
        )
        TimekeepingOrchestrator.create_time_entry(
            self.tenant.id,
            report.id,
            TimeEntryIn(date=date(2025, 1, 15), hours=Decimal("8")),
            self.user.id,
        )
        TimekeepingOrchestrator.submit_time_report(
            self.tenant.id, report.id, self.user.id
        )

        # Second submit on a non-DRAFT report must fail.
        try:
            TimekeepingOrchestrator.submit_time_report(
                self.tenant.id, report.id, self.user.id
            )
            raise AssertionError("expected Conflict")
        except Conflict:
            pass

        failures = AuditRepository.get_all(
            self.tenant.id, "time_report.submitted", None, None, None, "failure"
        )
        assert len(failures) == 1
        assert failures[0].resource_id == report.id
        assert failures[0].metadata["error_type"] == "Conflict"

    def test_lock_unknown_period_records_failure_audit(self):
        try:
            TimekeepingOrchestrator.lock_period(self.tenant.id, 999_999, self.user.id)
            raise AssertionError("expected NotFound")
        except NotFound:
            pass

        failures = AuditRepository.get_all(
            self.tenant.id, "period.locked", None, None, None, "failure"
        )
        assert len(failures) == 1
        assert failures[0].resource_id == 999_999
        assert failures[0].metadata["error_type"] == "NotFound"

    def test_failure_audit_survives_business_rollback(self):
        """The failure audit row must be written even though the business
        operation's transaction was rolled back."""
        with contextlib.suppress(NotFound):
            TimekeepingOrchestrator.lock_period(self.tenant.id, 12345, self.user.id)

        # No period was created (operation failed).
        assert TimekeepingRepository.get_period_by_id(12345) is None
        # But the failure audit was committed.
        failures = AuditRepository.get_all(
            self.tenant.id, "period.locked", None, None, None, "failure"
        )
        assert len(failures) == 1
