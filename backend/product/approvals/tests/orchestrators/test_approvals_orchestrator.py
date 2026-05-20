from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.common.exceptions import Conflict
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.services.tenants_service import TenantService
from product.approvals.dtos.dtos import RejectApprovalIn
from product.approvals.orchestrators.approvals_orchestrator import ApprovalsOrchestrator
from product.approvals.repositories.approvals_repository import ApprovalsRepository
from product.common.classes import ApprovalStatus, TimeReportStatus
from product.timekeeping.entities.timekeeping_entities import (
    PeriodEntity,
    TimeEntryEntity,
)
from product.timekeeping.repositories.timekeeping_repository import (
    TimekeepingRepository,
)
from product.workforce.entities.workforce_entities import (
    CreateEmployeeEntity,
    DepartmentEntity,
    RoleEntity,
)
from product.workforce.models import EmployeeModel
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


def make_employee(
    tenant_id: int, email: str = "emp@example.com", user_id: int | None = None
):
    dept = WorkforceService.create_department(
        tenant_id, DepartmentEntity(name=f"Dept-{email}")
    )
    role = WorkforceService.create_role(tenant_id, RoleEntity(name=f"Role-{email}"))
    employee = WorkforceService.create_employee(
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
    if user_id is not None:
        EmployeeModel.objects.filter(id=employee.id).update(user_id=user_id)
    return employee


def make_period(tenant_id: int, user_id: int):
    return TimekeepingRepository.create_period(
        PeriodEntity(
            name="April 2025",
            start_date=date(2025, 4, 1),
            end_date=date(2025, 4, 30),
        ),
        tenant_id,
        user_id=user_id,
    )


def make_report_with_entry(
    tenant_id: int, employee_id: int, period_id: int, user_id: int
):
    report = TimekeepingRepository.create_time_report(
        employee_id=employee_id,
        period_id=period_id,
        tenant_id=tenant_id,
        user_id=user_id,
    )
    TimekeepingRepository.create_time_entry(
        report.id,
        TimeEntryEntity(
            date=date(2025, 4, 1),
            hours=Decimal("8.00"),
            start_time=None,
            end_time=None,
            description="",
        ),
        user_id=user_id,
    )
    return report


class ApprovalsOrchestratorSubmitTransactionTests(TestCase):
    """Verify the orchestrator's transactional guarantees on submit."""

    def setUp(self):
        self.employee_user = make_user("emp@example.com")
        self.manager_user = make_user("mgr@example.com")
        self.tenant = make_tenant(self.manager_user.id)
        add_member(self.tenant.id, self.manager_user.id, MembershipRoles.ADMIN)
        add_member(self.tenant.id, self.employee_user.id, MembershipRoles.EMPLOYEE)
        self.employee = make_employee(self.tenant.id, user_id=self.employee_user.id)
        self.period = make_period(self.tenant.id, self.manager_user.id)
        self.report = make_report_with_entry(
            self.tenant.id,
            self.employee.id,
            self.period.id,
            self.employee_user.id,
        )

    def test_submit_rolls_back_when_create_approval_fails(self):
        with (
            patch(
                "product.approvals.orchestrators.approvals_orchestrator.ApprovalsService.create_submitted_approval",
                side_effect=Exception("DB error"),
            ),
            pytest.raises(Exception, match="DB error"),
        ):
            ApprovalsOrchestrator.submit_report_for_approval(
                self.tenant.id,
                self.report.id,
                user_id=self.employee_user.id,
            )

        report = TimekeepingRepository.get_time_report_by_id(self.report.id)
        assert report.status == str(TimeReportStatus.DRAFT)
        assert ApprovalsRepository.find_by_report_id(self.report.id) is None

    def test_submit_rolls_back_when_submit_time_report_fails(self):
        with (
            patch(
                "product.approvals.orchestrators.approvals_orchestrator.TimekeepingService.submit_time_report",
                side_effect=Exception("Status error"),
            ),
            pytest.raises(Exception, match="Status error"),
        ):
            ApprovalsOrchestrator.submit_report_for_approval(
                self.tenant.id,
                self.report.id,
                user_id=self.employee_user.id,
            )

        assert ApprovalsRepository.find_by_report_id(self.report.id) is None
        report = TimekeepingRepository.get_time_report_by_id(self.report.id)
        assert report.status == str(TimeReportStatus.DRAFT)


class ApprovalsOrchestratorApproveTransactionTests(TestCase):
    """Verify the orchestrator's transactional guarantees on approve."""

    def setUp(self):
        self.employee_user = make_user("emp@example.com")
        self.manager_user = make_user("mgr@example.com")
        self.tenant = make_tenant(self.manager_user.id)
        add_member(self.tenant.id, self.manager_user.id, MembershipRoles.ADMIN)
        add_member(self.tenant.id, self.employee_user.id, MembershipRoles.EMPLOYEE)
        self.employee = make_employee(self.tenant.id, user_id=self.employee_user.id)
        self.period = make_period(self.tenant.id, self.manager_user.id)
        self.report = make_report_with_entry(
            self.tenant.id,
            self.employee.id,
            self.period.id,
            self.employee_user.id,
        )
        self.approval = ApprovalsOrchestrator.submit_report_for_approval(
            self.tenant.id, self.report.id, user_id=self.employee_user.id
        )

    def test_approve_rolls_back_when_approve_approval_fails(self):
        with (
            patch(
                "product.approvals.orchestrators.approvals_orchestrator.ApprovalsService.approve_approval",
                side_effect=Exception("Boom"),
            ),
            pytest.raises(Exception, match="Boom"),
        ):
            ApprovalsOrchestrator.approve_report(
                self.tenant.id,
                self.approval.id,
                user_id=self.manager_user.id,
            )

        report = TimekeepingRepository.get_time_report_by_id(self.report.id)
        assert report.status == str(TimeReportStatus.SUBMITTED)
        approval = ApprovalsRepository.get_by_id(self.approval.id)
        assert approval.status == ApprovalStatus.PENDING.value

    def test_approve_rolls_back_when_approve_time_report_fails(self):
        with (
            patch(
                "product.approvals.orchestrators.approvals_orchestrator.TimekeepingService.approve_time_report",
                side_effect=Exception("Time report failed"),
            ),
            pytest.raises(Exception, match="Time report failed"),
        ):
            ApprovalsOrchestrator.approve_report(
                self.tenant.id,
                self.approval.id,
                user_id=self.manager_user.id,
            )

        approval = ApprovalsRepository.get_by_id(self.approval.id)
        assert approval.status == ApprovalStatus.PENDING.value


class ApprovalsOrchestratorRejectTransactionTests(TestCase):
    """Verify the orchestrator's transactional guarantees and entity validation on reject."""

    def setUp(self):
        self.employee_user = make_user("emp@example.com")
        self.manager_user = make_user("mgr@example.com")
        self.tenant = make_tenant(self.manager_user.id)
        add_member(self.tenant.id, self.manager_user.id, MembershipRoles.ADMIN)
        add_member(self.tenant.id, self.employee_user.id, MembershipRoles.EMPLOYEE)
        self.employee = make_employee(self.tenant.id, user_id=self.employee_user.id)
        self.period = make_period(self.tenant.id, self.manager_user.id)
        self.report = make_report_with_entry(
            self.tenant.id,
            self.employee.id,
            self.period.id,
            self.employee_user.id,
        )
        self.approval = ApprovalsOrchestrator.submit_report_for_approval(
            self.tenant.id, self.report.id, user_id=self.employee_user.id
        )

    def test_reject_rolls_back_when_reject_approval_fails(self):
        with (
            patch(
                "product.approvals.orchestrators.approvals_orchestrator.ApprovalsService.reject_approval",
                side_effect=Exception("Reject failed"),
            ),
            pytest.raises(Exception, match="Reject failed"),
        ):
            ApprovalsOrchestrator.reject_report(
                self.tenant.id,
                self.approval.id,
                RejectApprovalIn(reason="Bad data"),
                user_id=self.manager_user.id,
            )

        report = TimekeepingRepository.get_time_report_by_id(self.report.id)
        assert report.status == str(TimeReportStatus.SUBMITTED)
        approval = ApprovalsRepository.get_by_id(self.approval.id)
        assert approval.status == ApprovalStatus.PENDING.value

    def test_reject_strips_reason_via_entity_before_persisting(self):
        ApprovalsOrchestrator.reject_report(
            self.tenant.id,
            self.approval.id,
            RejectApprovalIn(reason="   Padded reason   "),
            user_id=self.manager_user.id,
        )

        report = TimekeepingRepository.get_time_report_by_id(self.report.id)
        assert report.rejection_reason == "Padded reason"

    def test_reject_raises_conflict_if_approval_not_pending(self):
        ApprovalsOrchestrator.approve_report(
            self.tenant.id, self.approval.id, user_id=self.manager_user.id
        )

        with pytest.raises(Conflict):
            ApprovalsOrchestrator.reject_report(
                self.tenant.id,
                self.approval.id,
                RejectApprovalIn(reason="Too late"),
                user_id=self.manager_user.id,
            )
