from datetime import UTC, date, datetime, time
from decimal import Decimal

import pytest
from django.test import TestCase
from django.utils import timezone as django_timezone

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.tenants.entities.tenant_entities import TenantEntity
from infra.tenants.services.tenants_service import TenantService
from product.common.classes import PeriodStatus, TimeReportStatus
from product.timekeeping.entities.timekeeping_entities import (
    PeriodEntity,
    TimeEntryEntity,
    TimeEntryUpdateEntity,
)
from product.timekeeping.repositories.timekeeping_repository import (
    TimekeepingRepository,
)
from product.workforce.dtos.dtos import DepartmentIn, EmployeeIn, RoleIn
from product.workforce.services.workforce_service import WorkforceService


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


class TimekeepingRepositoryPeriodTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)

    def test_create_period_persists_with_open_status(self):
        entity = PeriodEntity(
            name="April 2025",
            start_date=date(2025, 4, 1),
            end_date=date(2025, 4, 30),
        )

        period = TimekeepingRepository.create_period(
            entity, self.tenant.id, created_by_id=self.user.id
        )

        assert period.id is not None
        assert period.name == "April 2025"
        assert period.tenant_id == self.tenant.id
        assert period.status == PeriodStatus.OPEN.value
        assert period.created_by_id == self.user.id

    def test_create_period_raises_for_non_entity_payload(self):
        with pytest.raises(TypeError, match="Expected PeriodEntity"):
            TimekeepingRepository.create_period(
                "not-an-entity", self.tenant.id, created_by_id=self.user.id
            )

    def test_get_period_by_id_returns_period(self):
        created = TimekeepingRepository.create_period(
            PeriodEntity(
                name="April 2025",
                start_date=date(2025, 4, 1),
                end_date=date(2025, 4, 30),
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )

        found = TimekeepingRepository.get_period_by_id(created.id)

        assert found is not None
        assert found.id == created.id

    def test_get_period_by_id_returns_none_for_unknown_id(self):
        assert TimekeepingRepository.get_period_by_id(99999) is None

    def test_list_periods_orders_by_start_date_desc(self):
        TimekeepingRepository.create_period(
            PeriodEntity(
                name="January", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )
        TimekeepingRepository.create_period(
            PeriodEntity(
                name="February",
                start_date=date(2025, 2, 1),
                end_date=date(2025, 2, 28),
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )

        periods = TimekeepingRepository.list_periods(self.tenant.id)

        assert [p.name for p in periods] == ["February", "January"]

    def test_list_periods_filters_by_status(self):
        open_period = TimekeepingRepository.create_period(
            PeriodEntity(
                name="A", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )
        TimekeepingRepository.lock_period(
            open_period.id, self.user.id, django_timezone.now()
        )

        TimekeepingRepository.create_period(
            PeriodEntity(
                name="B", start_date=date(2025, 2, 1), end_date=date(2025, 2, 28)
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )

        locked = TimekeepingRepository.list_periods(
            self.tenant.id, status=PeriodStatus.LOCKED.value
        )
        opened = TimekeepingRepository.list_periods(
            self.tenant.id, status=PeriodStatus.OPEN.value
        )

        assert [p.name for p in locked] == ["A"]
        assert [p.name for p in opened] == ["B"]

    def test_list_periods_isolates_by_tenant(self):
        TimekeepingRepository.create_period(
            PeriodEntity(
                name="Mine", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, slug="other")
        TimekeepingRepository.create_period(
            PeriodEntity(
                name="Theirs",
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 31),
            ),
            other_tenant.id,
            created_by_id=other_user.id,
        )

        mine = TimekeepingRepository.list_periods(self.tenant.id)

        assert [p.name for p in mine] == ["Mine"]

    def test_find_period_by_name_is_case_insensitive(self):
        TimekeepingRepository.create_period(
            PeriodEntity(
                name="April 2025",
                start_date=date(2025, 4, 1),
                end_date=date(2025, 4, 30),
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )

        found = TimekeepingRepository.find_period_by_name(self.tenant.id, "april 2025")

        assert found is not None
        assert found.name == "April 2025"

    def test_find_period_by_name_returns_none_when_missing(self):
        assert (
            TimekeepingRepository.find_period_by_name(self.tenant.id, "ghost") is None
        )

    def test_find_overlapping_period_detects_overlap(self):
        TimekeepingRepository.create_period(
            PeriodEntity(
                name="April",
                start_date=date(2025, 4, 1),
                end_date=date(2025, 4, 30),
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )

        overlap = TimekeepingRepository.find_overlapping_period(
            self.tenant.id,
            start_date=date(2025, 4, 15),
            end_date=date(2025, 5, 15),
        )

        assert overlap is not None
        assert overlap.name == "April"

    def test_find_overlapping_period_returns_none_when_disjoint(self):
        TimekeepingRepository.create_period(
            PeriodEntity(
                name="April",
                start_date=date(2025, 4, 1),
                end_date=date(2025, 4, 30),
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )

        assert (
            TimekeepingRepository.find_overlapping_period(
                self.tenant.id,
                start_date=date(2025, 5, 1),
                end_date=date(2025, 5, 31),
            )
            is None
        )

    def test_find_overlapping_period_excludes_id(self):
        existing = TimekeepingRepository.create_period(
            PeriodEntity(
                name="April",
                start_date=date(2025, 4, 1),
                end_date=date(2025, 4, 30),
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )

        result = TimekeepingRepository.find_overlapping_period(
            self.tenant.id,
            start_date=date(2025, 4, 1),
            end_date=date(2025, 4, 30),
            exclude_id=existing.id,
        )

        assert result is None

    def test_lock_period_transitions_status(self):
        period = TimekeepingRepository.create_period(
            PeriodEntity(
                name="April",
                start_date=date(2025, 4, 1),
                end_date=date(2025, 4, 30),
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )
        locked_at = datetime(2025, 5, 1, tzinfo=UTC)

        locked = TimekeepingRepository.lock_period(period.id, self.user.id, locked_at)

        assert locked is not None
        assert locked.status == PeriodStatus.LOCKED.value
        assert locked.locked_by_id == self.user.id

    def test_lock_period_returns_none_if_already_locked(self):
        period = TimekeepingRepository.create_period(
            PeriodEntity(
                name="April",
                start_date=date(2025, 4, 1),
                end_date=date(2025, 4, 30),
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )
        TimekeepingRepository.lock_period(
            period.id, self.user.id, django_timezone.now()
        )

        result = TimekeepingRepository.lock_period(
            period.id, self.user.id, django_timezone.now()
        )

        assert result is None


class TimekeepingRepositoryReportTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        self.employee = make_employee(self.tenant.id)
        self.period = TimekeepingRepository.create_period(
            PeriodEntity(
                name="April 2025",
                start_date=date(2025, 4, 1),
                end_date=date(2025, 4, 30),
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )

    def test_create_time_report_persists(self):
        report = TimekeepingRepository.create_time_report(
            employee_id=self.employee.id,
            period_id=self.period.id,
            tenant_id=self.tenant.id,
            created_by_id=self.user.id,
        )

        assert report.id is not None
        assert report.employee_id == self.employee.id
        assert report.period_id == self.period.id
        assert report.tenant_id == self.tenant.id

    def test_get_time_report_by_id_returns_report(self):
        created = TimekeepingRepository.create_time_report(
            employee_id=self.employee.id,
            period_id=self.period.id,
            tenant_id=self.tenant.id,
            created_by_id=self.user.id,
        )

        found = TimekeepingRepository.get_time_report_by_id(created.id)

        assert found is not None
        assert found.id == created.id

    def test_get_time_report_by_id_returns_none_for_unknown(self):
        assert TimekeepingRepository.get_time_report_by_id(99999) is None

    def test_get_report_status_returns_enum(self):
        created = TimekeepingRepository.create_time_report(
            employee_id=self.employee.id,
            period_id=self.period.id,
            tenant_id=self.tenant.id,
            created_by_id=self.user.id,
        )

        status = TimekeepingRepository.get_report_status(created.id)

        assert status == TimeReportStatus.DRAFT

    def test_get_report_status_returns_none_for_missing_report(self):
        assert TimekeepingRepository.get_report_status(99999) is None

    def test_find_report_by_employee_and_period(self):
        TimekeepingRepository.create_time_report(
            employee_id=self.employee.id,
            period_id=self.period.id,
            tenant_id=self.tenant.id,
            created_by_id=self.user.id,
        )

        found = TimekeepingRepository.find_report_by_employee_and_period(
            self.employee.id, self.period.id
        )

        assert found is not None
        assert found.employee_id == self.employee.id
        assert found.period_id == self.period.id

    def test_find_report_by_employee_and_period_returns_none_when_missing(self):
        assert (
            TimekeepingRepository.find_report_by_employee_and_period(
                self.employee.id, self.period.id
            )
            is None
        )

    def test_list_time_reports_filters_by_period_and_employee(self):
        other_employee = make_employee(self.tenant.id, "other-emp@example.com")
        other_period = TimekeepingRepository.create_period(
            PeriodEntity(
                name="May 2025",
                start_date=date(2025, 5, 1),
                end_date=date(2025, 5, 31),
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )

        r1 = TimekeepingRepository.create_time_report(
            employee_id=self.employee.id,
            period_id=self.period.id,
            tenant_id=self.tenant.id,
            created_by_id=self.user.id,
        )
        TimekeepingRepository.create_time_report(
            employee_id=other_employee.id,
            period_id=self.period.id,
            tenant_id=self.tenant.id,
            created_by_id=self.user.id,
        )
        TimekeepingRepository.create_time_report(
            employee_id=self.employee.id,
            period_id=other_period.id,
            tenant_id=self.tenant.id,
            created_by_id=self.user.id,
        )

        by_employee = TimekeepingRepository.list_time_reports(
            self.tenant.id, employee_id=self.employee.id
        )
        by_employee_and_period = TimekeepingRepository.list_time_reports(
            self.tenant.id,
            employee_id=self.employee.id,
            period_id=self.period.id,
        )

        assert len(by_employee) == 2
        assert len(by_employee_and_period) == 1
        assert by_employee_and_period[0].id == r1.id

    def test_update_time_report_status_writes_optional_fields(self):
        report = TimekeepingRepository.create_time_report(
            employee_id=self.employee.id,
            period_id=self.period.id,
            tenant_id=self.tenant.id,
            created_by_id=self.user.id,
        )
        submitted_at = datetime(2025, 4, 30, 10, tzinfo=UTC)

        updated = TimekeepingRepository.update_time_report_status(
            report.id,
            new_status=TimeReportStatus.SUBMITTED.value,
            updated_by_id=self.user.id,
            submitted_at=submitted_at,
        )

        assert updated is not None
        assert updated.status == TimeReportStatus.SUBMITTED.value
        assert updated.updated_by_id == self.user.id
        assert updated.submitted_at == submitted_at

    def test_update_time_report_status_returns_none_for_unknown_report(self):
        result = TimekeepingRepository.update_time_report_status(
            99999, new_status=TimeReportStatus.APPROVED.value
        )

        assert result is None

    def test_update_time_report_status_writes_rejection_reason(self):
        report = TimekeepingRepository.create_time_report(
            employee_id=self.employee.id,
            period_id=self.period.id,
            tenant_id=self.tenant.id,
            created_by_id=self.user.id,
        )

        updated = TimekeepingRepository.update_time_report_status(
            report.id,
            new_status=TimeReportStatus.REJECTED.value,
            rejection_reason="Bad data",
            rejected_at=django_timezone.now(),
        )

        assert updated is not None
        assert updated.rejection_reason == "Bad data"


class TimekeepingRepositoryEntryTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        self.employee = make_employee(self.tenant.id)
        self.period = TimekeepingRepository.create_period(
            PeriodEntity(
                name="April 2025",
                start_date=date(2025, 4, 1),
                end_date=date(2025, 4, 30),
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )
        self.report = TimekeepingRepository.create_time_report(
            employee_id=self.employee.id,
            period_id=self.period.id,
            tenant_id=self.tenant.id,
            created_by_id=self.user.id,
        )

    def test_create_time_entry_persists(self):
        entity = TimeEntryEntity(
            date=date(2025, 4, 1),
            hours=Decimal("8.00"),
            start_time=time(9, 0),
            end_time=time(17, 0),
            description="Worked",
        )

        entry = TimekeepingRepository.create_time_entry(
            self.report.id, entity, created_by_id=self.user.id
        )

        assert entry.id is not None
        assert entry.report_id == self.report.id
        assert entry.hours == Decimal("8.00")
        assert entry.description == "Worked"

    def test_create_time_entry_raises_for_non_entity(self):
        with pytest.raises(TypeError, match="Expected TimeEntryEntity"):
            TimekeepingRepository.create_time_entry(
                self.report.id, "not-an-entity", created_by_id=self.user.id
            )

    def test_get_time_entry_by_id_returns_entry(self):
        entry = TimekeepingRepository.create_time_entry(
            self.report.id,
            TimeEntryEntity(date=date(2025, 4, 1), hours=Decimal("8.00")),
            created_by_id=self.user.id,
        )

        found = TimekeepingRepository.get_time_entry_by_id(entry.id)

        assert found is not None
        assert found.id == entry.id

    def test_get_time_entry_by_id_returns_none_for_unknown(self):
        assert TimekeepingRepository.get_time_entry_by_id(99999) is None

    def test_list_time_entries_orders_by_date(self):
        TimekeepingRepository.create_time_entry(
            self.report.id,
            TimeEntryEntity(date=date(2025, 4, 3), hours=Decimal("8")),
            created_by_id=self.user.id,
        )
        TimekeepingRepository.create_time_entry(
            self.report.id,
            TimeEntryEntity(date=date(2025, 4, 1), hours=Decimal("8")),
            created_by_id=self.user.id,
        )
        TimekeepingRepository.create_time_entry(
            self.report.id,
            TimeEntryEntity(date=date(2025, 4, 2), hours=Decimal("8")),
            created_by_id=self.user.id,
        )

        entries = TimekeepingRepository.list_time_entries(self.report.id)

        assert [e.date for e in entries] == [
            date(2025, 4, 1),
            date(2025, 4, 2),
            date(2025, 4, 3),
        ]

    def test_update_time_entry_persists_changes(self):
        entry = TimekeepingRepository.create_time_entry(
            self.report.id,
            TimeEntryEntity(date=date(2025, 4, 1), hours=Decimal("4")),
            created_by_id=self.user.id,
        )

        updated = TimekeepingRepository.update_time_entry(
            TimeEntryUpdateEntity(
                entry_id=entry.id,
                date=date(2025, 4, 1),
                hours=Decimal("8"),
                description="Updated",
            ),
            updated_by_id=self.user.id,
        )

        assert updated.hours == Decimal("8")
        assert updated.description == "Updated"
        assert updated.updated_by_id == self.user.id

    def test_update_time_entry_raises_type_error_for_non_entity_payload(self):
        with pytest.raises(TypeError, match="Expected TimeEntryUpdateEntity"):
            TimekeepingRepository.update_time_entry("not-an-entity")

    def test_delete_time_entry_returns_true_when_deleted(self):
        entry = TimekeepingRepository.create_time_entry(
            self.report.id,
            TimeEntryEntity(date=date(2025, 4, 1), hours=Decimal("4")),
            created_by_id=self.user.id,
        )

        assert TimekeepingRepository.delete_time_entry(entry.id) is True
        assert TimekeepingRepository.get_time_entry_by_id(entry.id) is None

    def test_delete_time_entry_returns_false_when_missing(self):
        assert TimekeepingRepository.delete_time_entry(99999) is False


class TimekeepingRepositoryHistoryTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        self.employee = make_employee(self.tenant.id)
        self.period = TimekeepingRepository.create_period(
            PeriodEntity(
                name="April 2025",
                start_date=date(2025, 4, 1),
                end_date=date(2025, 4, 30),
            ),
            self.tenant.id,
            created_by_id=self.user.id,
        )
        self.report = TimekeepingRepository.create_time_report(
            employee_id=self.employee.id,
            period_id=self.period.id,
            tenant_id=self.tenant.id,
            created_by_id=self.user.id,
        )

    def test_create_status_history_persists(self):
        history = TimekeepingRepository.create_status_history(
            report_id=self.report.id,
            from_status=TimeReportStatus.DRAFT.value,
            to_status=TimeReportStatus.SUBMITTED.value,
            changed_by_id=self.user.id,
            reason="Submitting",
        )

        assert history.id is not None
        assert history.from_status == TimeReportStatus.DRAFT.value
        assert history.to_status == TimeReportStatus.SUBMITTED.value
        assert history.reason == "Submitting"

    def test_list_status_history_orders_by_changed_at(self):
        TimekeepingRepository.create_status_history(
            report_id=self.report.id,
            from_status=None,
            to_status=TimeReportStatus.DRAFT.value,
            changed_by_id=self.user.id,
        )
        TimekeepingRepository.create_status_history(
            report_id=self.report.id,
            from_status=TimeReportStatus.DRAFT.value,
            to_status=TimeReportStatus.SUBMITTED.value,
            changed_by_id=self.user.id,
        )

        history = TimekeepingRepository.list_status_history(self.report.id)

        assert len(history) == 2
        assert history[0].to_status == TimeReportStatus.DRAFT.value
        assert history[1].to_status == TimeReportStatus.SUBMITTED.value

    def test_create_entry_change_history_persists(self):
        entry = TimekeepingRepository.create_time_entry(
            self.report.id,
            TimeEntryEntity(date=date(2025, 4, 1), hours=Decimal("4")),
            created_by_id=self.user.id,
        )

        history = TimekeepingRepository.create_entry_change_history(
            entry_id=entry.id,
            field_name="hours",
            old_value="4",
            new_value="8",
            changed_by_id=self.user.id,
        )

        assert history.id is not None
        assert history.field_name == "hours"
        assert history.old_value == "4"
        assert history.new_value == "8"

    def test_list_entry_change_history_returns_changes_for_entry(self):
        entry = TimekeepingRepository.create_time_entry(
            self.report.id,
            TimeEntryEntity(date=date(2025, 4, 1), hours=Decimal("4")),
            created_by_id=self.user.id,
        )
        TimekeepingRepository.create_entry_change_history(
            entry_id=entry.id,
            field_name="hours",
            old_value="4",
            new_value="6",
            changed_by_id=self.user.id,
        )
        TimekeepingRepository.create_entry_change_history(
            entry_id=entry.id,
            field_name="hours",
            old_value="6",
            new_value="8",
            changed_by_id=self.user.id,
        )

        history = TimekeepingRepository.list_entry_change_history(entry.id)

        assert len(history) == 2
        assert [(h.old_value, h.new_value) for h in history] == [("4", "6"), ("6", "8")]
