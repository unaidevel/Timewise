from datetime import date
from decimal import Decimal

import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.common.exceptions import Conflict, Forbidden, NotFound
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.services.tenants_service import TenantService
from product.approvals.dtos.dtos import RejectApprovalIn
from product.approvals.orchestrators.approvals_orchestrator import ApprovalsOrchestrator
from product.approvals.services.approvals_service import ApprovalsService
from product.common.classes import ApprovalStatus, TimeReportStatus
from product.timekeeping.entities.timekeeping_entities import PeriodEntity
from product.timekeeping.models import TimeReportModel
from product.timekeeping.repositories.timekeeping_repository import (
    TimekeepingRepository,
)
from product.workforce.entities.workforce_entities import (
    CreateEmployeeEntity,
    DepartmentEntity,
    RoleEntity,
)
from product.workforce.services.workforce_service import WorkforceService


def make_user(email: str = "owner@example.com"):
    return AuthRepository.create_user(
        email=email,
        full_name="Test User",
        password_hash=AuthService._hash_password("SecurePass123!"),
    )


def make_tenant(user_id: int, slug: str = "acme"):
    return TenantService.create(
        TenantEntity(name="Acme Corp", slug=slug), user_id=user_id
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
        tenant_id, DepartmentEntity(name=f"Dept-{email}")
    )
    role = WorkforceService.create_role(tenant_id, RoleEntity(name=f"Role-{email}"))
    return WorkforceService.create_employee(
        tenant_id,
        CreateEmployeeEntity(
            full_name="Test Employee",
            email=email,
            department_id=dept.id,
            role_id=role.id,
            hourly_rate=Decimal("25.00"),
            contract_hours_per_week=40,
            hired_at=date(2024, 1, 1),
        ),
    )


def make_period(tenant_id: int, user_id: int):
    entity = PeriodEntity(
        name="April 2025", start_date=date(2025, 4, 1), end_date=date(2025, 4, 30)
    )
    return TimekeepingRepository.create_period(entity, tenant_id, user_id=user_id)


def make_report_with_entry(
    tenant_id: int, employee_id: int, period_id: int, user_id: int
):
    report = TimekeepingRepository.create_time_report(
        employee_id=employee_id,
        period_id=period_id,
        tenant_id=tenant_id,
        user_id=user_id,
    )
    from product.timekeeping.entities.timekeeping_entities import TimeEntryEntity

    entry = TimeEntryEntity(
        date=date(2025, 4, 1),
        hours=Decimal("8.00"),
        start_time=None,
        end_time=None,
        description="",
    )
    TimekeepingRepository.create_time_entry(report.id, entry, user_id=user_id)
    return report


class ApprovalsServiceSubmitTests(TestCase):
    def setUp(self):
        self.employee_user = make_user("emp@example.com")
        self.manager_user = make_user("mgr@example.com")
        self.tenant = make_tenant(self.manager_user.id)
        add_member(self.tenant.id, self.manager_user.id, MembershipRoles.MANAGER)
        add_member(self.tenant.id, self.employee_user.id, MembershipRoles.EMPLOYEE)
        self.employee = make_employee(self.tenant.id)
        self.period = make_period(self.tenant.id, self.manager_user.id)
        self.report = make_report_with_entry(
            self.tenant.id, self.employee.id, self.period.id, self.employee_user.id
        )

    def test_submit_creates_approval_record_and_event(self):
        approval = ApprovalsOrchestrator.submit_report_for_approval(
            self.tenant.id, self.report.id, user_id=self.employee_user.id
        )

        self.assertEqual(approval.tenant_id, self.tenant.id)
        self.assertEqual(approval.report_id, self.report.id)
        self.assertEqual(approval.status, ApprovalStatus.PENDING.value)

        events = ApprovalsService.list_approval_events(
            self.tenant.id, approval.id, user_id=self.employee_user.id
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].action, "submitted")

    def test_submit_updates_time_report_status_to_submitted(self):
        ApprovalsOrchestrator.submit_report_for_approval(
            self.tenant.id, self.report.id, user_id=self.employee_user.id
        )

        report = TimekeepingRepository.get_time_report_by_id(self.report.id)
        self.assertEqual(report.status, str(TimeReportStatus.SUBMITTED))

    def test_submit_raises_if_report_not_in_draft(self):
        ApprovalsOrchestrator.submit_report_for_approval(
            self.tenant.id, self.report.id, user_id=self.employee_user.id
        )

        with pytest.raises(Conflict, match="status"):
            ApprovalsOrchestrator.submit_report_for_approval(
                self.tenant.id, self.report.id, user_id=self.employee_user.id
            )

    def test_submit_raises_if_report_not_found(self):
        with pytest.raises(NotFound):
            ApprovalsOrchestrator.submit_report_for_approval(
                self.tenant.id, 99999, user_id=self.employee_user.id
            )

    def test_submit_raises_if_report_is_empty(self):
        other_employee = make_employee(self.tenant.id, "other-emp@example.com")
        empty_report = TimekeepingRepository.create_time_report(
            employee_id=other_employee.id,
            period_id=self.period.id,
            tenant_id=self.tenant.id,
            user_id=self.employee_user.id,
        )
        with pytest.raises(Conflict, match="empty"):
            ApprovalsOrchestrator.submit_report_for_approval(
                self.tenant.id, empty_report.id, user_id=self.employee_user.id
            )

    def test_submit_raises_if_approval_already_exists(self):
        ApprovalsOrchestrator.submit_report_for_approval(
            self.tenant.id, self.report.id, user_id=self.employee_user.id
        )
        TimeReportModel.objects.filter(id=self.report.id).update(
            status=str(TimeReportStatus.DRAFT)
        )
        with pytest.raises(Conflict, match="already exists"):
            ApprovalsOrchestrator.submit_report_for_approval(
                self.tenant.id, self.report.id, user_id=self.employee_user.id
            )


class ApprovalsServiceApproveRejectTests(TestCase):
    def setUp(self):
        self.employee_user = make_user("emp@example.com")
        self.manager_user = make_user("mgr@example.com")
        self.tenant = make_tenant(self.manager_user.id)
        add_member(self.tenant.id, self.manager_user.id, MembershipRoles.MANAGER)
        add_member(self.tenant.id, self.employee_user.id, MembershipRoles.EMPLOYEE)
        self.employee = make_employee(self.tenant.id)
        self.period = make_period(self.tenant.id, self.manager_user.id)
        self.report = make_report_with_entry(
            self.tenant.id, self.employee.id, self.period.id, self.employee_user.id
        )
        self.approval = ApprovalsOrchestrator.submit_report_for_approval(
            self.tenant.id, self.report.id, user_id=self.employee_user.id
        )

    def test_approve_sets_status_and_creates_event(self):
        updated = ApprovalsOrchestrator.approve_report(
            self.tenant.id, self.approval.id, user_id=self.manager_user.id
        )

        self.assertEqual(updated.status, ApprovalStatus.APPROVED.value)
        self.assertEqual(updated.reviewer_id, self.manager_user.id)
        self.assertIsNotNone(updated.reviewed_at)

        report = TimekeepingRepository.get_time_report_by_id(self.report.id)
        self.assertEqual(report.status, str(TimeReportStatus.APPROVED))

        events = ApprovalsService.list_approval_events(
            self.tenant.id, self.approval.id, user_id=self.manager_user.id
        )
        self.assertEqual(events[-1].action, "approved")

    def test_reject_sets_status_reason_and_creates_event(self):
        updated = ApprovalsOrchestrator.reject_report(
            self.tenant.id,
            self.approval.id,
            RejectApprovalIn(reason="Missing entries"),
            user_id=self.manager_user.id,
        )

        self.assertEqual(updated.status, ApprovalStatus.REJECTED.value)
        self.assertEqual(updated.reviewer_id, self.manager_user.id)

        report = TimekeepingRepository.get_time_report_by_id(self.report.id)
        self.assertEqual(report.status, str(TimeReportStatus.REJECTED))
        self.assertEqual(report.rejection_reason, "Missing entries")

        events = ApprovalsService.list_approval_events(
            self.tenant.id, self.approval.id, user_id=self.manager_user.id
        )
        self.assertEqual(events[-1].action, "rejected")
        self.assertEqual(events[-1].reason, "Missing entries")

    def test_approve_raises_if_already_approved(self):
        ApprovalsOrchestrator.approve_report(
            self.tenant.id, self.approval.id, user_id=self.manager_user.id
        )

        with pytest.raises(Conflict, match="status"):
            ApprovalsOrchestrator.approve_report(
                self.tenant.id, self.approval.id, user_id=self.manager_user.id
            )

    def test_reject_raises_if_already_rejected(self):
        ApprovalsOrchestrator.reject_report(
            self.tenant.id,
            self.approval.id,
            RejectApprovalIn(reason="Bad data"),
            user_id=self.manager_user.id,
        )

        with pytest.raises(Conflict, match="status"):
            ApprovalsOrchestrator.reject_report(
                self.tenant.id,
                self.approval.id,
                RejectApprovalIn(reason="Again"),
                user_id=self.manager_user.id,
            )

    def test_approve_requires_manager_role(self):
        with pytest.raises(Forbidden):
            ApprovalsOrchestrator.approve_report(
                self.tenant.id, self.approval.id, user_id=self.employee_user.id
            )

    def test_reject_requires_manager_role(self):
        with pytest.raises(Forbidden):
            ApprovalsOrchestrator.reject_report(
                self.tenant.id,
                self.approval.id,
                RejectApprovalIn(reason="Nope"),
                user_id=self.employee_user.id,
            )

    def test_approve_raises_if_approval_not_found(self):
        with pytest.raises(NotFound):
            ApprovalsOrchestrator.approve_report(
                self.tenant.id, 99999, user_id=self.manager_user.id
            )

    def test_approve_raises_if_belongs_to_other_tenant(self):
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, slug="other")
        add_member(other_tenant.id, other_user.id, MembershipRoles.MANAGER)

        with pytest.raises(NotFound):
            ApprovalsOrchestrator.approve_report(
                other_tenant.id, self.approval.id, user_id=other_user.id
            )

    def test_reject_strips_whitespace_from_reason(self):
        ApprovalsOrchestrator.reject_report(
            self.tenant.id,
            self.approval.id,
            RejectApprovalIn(reason="  Too many gaps  "),
            user_id=self.manager_user.id,
        )

        report = TimekeepingRepository.get_time_report_by_id(self.report.id)
        self.assertEqual(report.rejection_reason, "Too many gaps")


class ApprovalsServiceListGetTests(TestCase):
    def setUp(self):
        self.employee_user = make_user("emp@example.com")
        self.manager_user = make_user("mgr@example.com")
        self.tenant = make_tenant(self.manager_user.id)
        add_member(self.tenant.id, self.manager_user.id, MembershipRoles.MANAGER)
        add_member(self.tenant.id, self.employee_user.id, MembershipRoles.EMPLOYEE)
        self.employee = make_employee(self.tenant.id)
        self.period = make_period(self.tenant.id, self.manager_user.id)
        self.report = make_report_with_entry(
            self.tenant.id, self.employee.id, self.period.id, self.employee_user.id
        )
        self.approval = ApprovalsOrchestrator.submit_report_for_approval(
            self.tenant.id, self.report.id, user_id=self.employee_user.id
        )

    def test_get_approval_returns_correct_record(self):
        found = ApprovalsService.get_approval(
            self.tenant.id, self.approval.id, user_id=self.employee_user.id
        )
        self.assertEqual(found.id, self.approval.id)

    def test_get_approval_raises_if_not_found(self):
        with pytest.raises(NotFound):
            ApprovalsService.get_approval(
                self.tenant.id, 99999, user_id=self.employee_user.id
            )

    def test_get_approval_raises_if_belongs_to_other_tenant(self):
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, slug="other")
        add_member(other_tenant.id, other_user.id, MembershipRoles.EMPLOYEE)

        with pytest.raises(NotFound):
            ApprovalsService.get_approval(
                other_tenant.id, self.approval.id, user_id=other_user.id
            )

    def test_list_approvals_returns_all_for_tenant(self):
        approvals = ApprovalsService.list_approvals(
            self.tenant.id, user_id=self.manager_user.id
        )
        self.assertEqual(len(approvals), 1)

    def test_list_approvals_filters_by_status(self):
        ApprovalsOrchestrator.approve_report(
            self.tenant.id, self.approval.id, user_id=self.manager_user.id
        )

        pending = ApprovalsService.list_approvals(
            self.tenant.id,
            user_id=self.manager_user.id,
            status=ApprovalStatus.PENDING.value,
        )
        approved = ApprovalsService.list_approvals(
            self.tenant.id,
            user_id=self.manager_user.id,
            status=ApprovalStatus.APPROVED.value,
        )

        self.assertEqual(len(pending), 0)
        self.assertEqual(len(approved), 1)

    def test_list_approval_events_returns_event_trail(self):
        ApprovalsOrchestrator.approve_report(
            self.tenant.id, self.approval.id, user_id=self.manager_user.id
        )

        events = ApprovalsService.list_approval_events(
            self.tenant.id, self.approval.id, user_id=self.manager_user.id
        )

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].action, "submitted")
        self.assertEqual(events[1].action, "approved")
