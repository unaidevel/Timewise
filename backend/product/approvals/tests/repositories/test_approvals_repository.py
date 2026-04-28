from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.services.tenants_service import TenantService
from product.approvals.entities.approval_entities import (
    APPROVAL_ACTION_APPROVED,
    APPROVAL_ACTION_SUBMITTED,
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_PENDING,
)
from product.approvals.repositories.approvals_repository import ApprovalsRepository
from product.timekeeping.entities.timekeeping_entities import PeriodEntity
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


def make_period(tenant_id: int, user_id: int, name: str = "April 2025"):
    entity = PeriodEntity(
        name=name, start_date=date(2025, 4, 1), end_date=date(2025, 4, 30)
    )
    return TimekeepingRepository.create_period(entity, tenant_id, created_by_id=user_id)


def make_report(tenant_id: int, employee_id: int, period_id: int, user_id: int):
    return TimekeepingRepository.create_time_report(
        employee_id=employee_id,
        period_id=period_id,
        tenant_id=tenant_id,
        created_by_id=user_id,
    )


class ApprovalsRepositoryTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        add_member(self.tenant.id, self.user.id, MembershipRoles.OWNER)
        self.employee = make_employee(self.tenant.id)
        self.period = make_period(self.tenant.id, self.user.id)
        self.report = make_report(
            self.tenant.id, self.employee.id, self.period.id, self.user.id
        )

    def test_create_approval_persists_with_pending_status(self):
        approval = ApprovalsRepository.create_approval(
            tenant_id=self.tenant.id,
            report_id=self.report.id,
            created_by_id=self.user.id,
        )

        self.assertEqual(approval.tenant_id, self.tenant.id)
        self.assertEqual(approval.report_id, self.report.id)
        self.assertEqual(approval.status, APPROVAL_STATUS_PENDING)
        self.assertIsNone(approval.reviewer_id)
        self.assertIsNone(approval.reviewed_at)

    def test_find_by_report_id_returns_approval(self):
        created = ApprovalsRepository.create_approval(
            tenant_id=self.tenant.id,
            report_id=self.report.id,
            created_by_id=self.user.id,
        )

        found = ApprovalsRepository.find_by_report_id(self.report.id)

        self.assertIsNotNone(found)
        self.assertEqual(found.id, created.id)

    def test_find_by_report_id_returns_none_when_missing(self):
        self.assertIsNone(ApprovalsRepository.find_by_report_id(99999))

    def test_find_by_id_returns_approval(self):
        created = ApprovalsRepository.create_approval(
            tenant_id=self.tenant.id,
            report_id=self.report.id,
            created_by_id=self.user.id,
        )

        found = ApprovalsRepository.find_by_id(created.id)

        self.assertIsNotNone(found)
        self.assertEqual(found.id, created.id)

    def test_list_by_tenant_is_scoped_to_tenant(self):
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, slug="other")
        add_member(other_tenant.id, other_user.id, MembershipRoles.OWNER)
        other_employee = make_employee(other_tenant.id, "other-emp@example.com")
        other_period = make_period(
            other_tenant.id, other_user.id, name="Other April 2025"
        )
        other_report = make_report(
            other_tenant.id, other_employee.id, other_period.id, other_user.id
        )

        ApprovalsRepository.create_approval(
            tenant_id=self.tenant.id,
            report_id=self.report.id,
            created_by_id=self.user.id,
        )
        ApprovalsRepository.create_approval(
            tenant_id=other_tenant.id,
            report_id=other_report.id,
            created_by_id=other_user.id,
        )

        result = ApprovalsRepository.list_by_tenant(self.tenant.id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].tenant_id, self.tenant.id)

    def test_list_by_tenant_filters_by_status(self):
        approval = ApprovalsRepository.create_approval(
            tenant_id=self.tenant.id,
            report_id=self.report.id,
            created_by_id=self.user.id,
        )
        ApprovalsRepository.update_approval_status(
            approval.id,
            new_status=APPROVAL_STATUS_APPROVED,
            reviewer_id=self.user.id,
        )

        pending = ApprovalsRepository.list_by_tenant(
            self.tenant.id, status=APPROVAL_STATUS_PENDING
        )
        approved = ApprovalsRepository.list_by_tenant(
            self.tenant.id, status=APPROVAL_STATUS_APPROVED
        )

        self.assertEqual(len(pending), 0)
        self.assertEqual(len(approved), 1)

    def test_update_approval_status_sets_reviewer_and_reviewed_at(self):
        approval = ApprovalsRepository.create_approval(
            tenant_id=self.tenant.id,
            report_id=self.report.id,
            created_by_id=self.user.id,
        )
        reviewed_at = timezone.now()

        updated = ApprovalsRepository.update_approval_status(
            approval.id,
            new_status=APPROVAL_STATUS_APPROVED,
            reviewer_id=self.user.id,
            reviewed_at=reviewed_at,
        )

        self.assertEqual(updated.status, APPROVAL_STATUS_APPROVED)
        self.assertEqual(updated.reviewer_id, self.user.id)
        self.assertIsNotNone(updated.reviewed_at)

    def test_update_approval_status_returns_none_when_not_found(self):
        result = ApprovalsRepository.update_approval_status(
            99999, new_status=APPROVAL_STATUS_APPROVED
        )
        self.assertIsNone(result)

    def test_create_event_persists_action_and_actor(self):
        approval = ApprovalsRepository.create_approval(
            tenant_id=self.tenant.id,
            report_id=self.report.id,
            created_by_id=self.user.id,
        )

        event = ApprovalsRepository.create_event(
            approval_id=approval.id,
            action=APPROVAL_ACTION_SUBMITTED,
            actor_id=self.user.id,
        )

        self.assertEqual(event.approval_id, approval.id)
        self.assertEqual(event.action, APPROVAL_ACTION_SUBMITTED)
        self.assertEqual(event.actor_id, self.user.id)
        self.assertEqual(event.reason, "")

    def test_list_events_returns_events_in_chronological_order(self):
        approval = ApprovalsRepository.create_approval(
            tenant_id=self.tenant.id,
            report_id=self.report.id,
            created_by_id=self.user.id,
        )
        ApprovalsRepository.create_event(
            approval_id=approval.id,
            action=APPROVAL_ACTION_SUBMITTED,
            actor_id=self.user.id,
        )
        ApprovalsRepository.create_event(
            approval_id=approval.id,
            action=APPROVAL_ACTION_APPROVED,
            actor_id=self.user.id,
        )

        events = ApprovalsRepository.list_events(approval.id)

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].action, APPROVAL_ACTION_SUBMITTED)
        self.assertEqual(events[1].action, APPROVAL_ACTION_APPROVED)
