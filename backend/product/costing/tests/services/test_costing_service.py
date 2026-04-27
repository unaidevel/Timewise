from datetime import date
from decimal import Decimal

import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.common.exceptions import Conflict, Forbidden, NotFound, UnprocessableEntity
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.services.tenants_service import TenantService
from product.common.classes import TimeReportStatus
from product.costing.dtos.dtos import OvertimeRuleIn, OvertimeRuleUpdate
from product.costing.services.costing_service import CostingService
from product.timekeeping.dtos.dtos import PeriodIn, TimeEntryIn, TimeReportIn
from product.timekeeping.services.timekeeping_service import TimekeepingService
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
    dept = WorkforceService.create_department(tenant_id, DepartmentIn(name=f"Dept-{email}"))
    role = WorkforceService.create_role(tenant_id, RoleIn(name=f"Role-{email}"))
    return WorkforceService.create_employee(
        tenant_id,
        EmployeeIn(
            full_name="Test Employee",
            email=email,
            department_id=dept.id,
            role_id=role.id,
            hourly_rate=Decimal("20.00"),
            contract_hours_per_week=40,
            hired_at=date(2024, 1, 1),
        ),
    )


def make_approved_report(tenant_id: int, employee_id: int, user_id: int):
    period = TimekeepingService.create_period(
        tenant_id,
        PeriodIn(name="Q1 2025", start_date=date(2025, 1, 1), end_date=date(2025, 3, 31)),
        user_id,
    )
    report = TimekeepingService.create_time_report(
        tenant_id, period.id, TimeReportIn(employee_id=employee_id), user_id
    )
    TimekeepingService.create_time_entry(
        tenant_id,
        report.id,
        TimeEntryIn(date=date(2025, 1, 6), hours=Decimal("8.00")),
        user_id,
    )
    TimekeepingService.submit_time_report(tenant_id, report.id, user_id)
    return TimekeepingService.approve_time_report(tenant_id, report.id, user_id)


def make_rule_payload(name: str = "Weekend rule") -> OvertimeRuleIn:
    return OvertimeRuleIn(
        name=name,
        multiplier=Decimal("1.50"),
        priority=1,
        conditions=[{"condition_type": "day_of_week", "value": "6,7"}],
    )


class CostingServiceRulesTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        add_member(self.tenant.id, self.user.id, MembershipRoles.OWNER)

    def test_create_rule_succeeds_and_returns_dto(self):
        rule = CostingService.create_rule(
            self.tenant.id, make_rule_payload(), user_id=self.user.id
        )
        assert rule.name == "Weekend rule"
        assert rule.multiplier == Decimal("1.50")
        assert rule.tenant_id == self.tenant.id
        assert rule.is_active is True
        assert len(rule.conditions) == 1

    def test_create_rule_raises_conflict_on_duplicate_name(self):
        CostingService.create_rule(
            self.tenant.id, make_rule_payload("Overtime"), user_id=self.user.id
        )
        with pytest.raises(Conflict, match="Overtime"):
            CostingService.create_rule(
                self.tenant.id,
                make_rule_payload("  OVERTIME  "),
                user_id=self.user.id,
            )

    def test_create_rule_allows_same_name_in_different_tenants(self):
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, "other")
        add_member(other_tenant.id, other_user.id, MembershipRoles.OWNER)

        CostingService.create_rule(
            self.tenant.id, make_rule_payload("Overtime"), user_id=self.user.id
        )
        rule = CostingService.create_rule(
            other_tenant.id, make_rule_payload("Overtime"), user_id=other_user.id
        )
        assert rule.tenant_id == other_tenant.id

    def test_get_rule_raises_not_found_for_wrong_tenant(self):
        rule = CostingService.create_rule(
            self.tenant.id, make_rule_payload(), user_id=self.user.id
        )
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, "other")
        add_member(other_tenant.id, other_user.id, MembershipRoles.OWNER)

        with pytest.raises(NotFound):
            CostingService.get_rule(other_tenant.id, rule.id, user_id=other_user.id)

    def test_list_rules_returns_only_tenant_rules(self):
        CostingService.create_rule(
            self.tenant.id, make_rule_payload("My Rule"), user_id=self.user.id
        )
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, "other")
        add_member(other_tenant.id, other_user.id, MembershipRoles.OWNER)
        CostingService.create_rule(
            other_tenant.id, make_rule_payload("Other Rule"), user_id=other_user.id
        )

        rules = CostingService.list_rules(self.tenant.id, user_id=self.user.id)
        assert len(rules) == 1
        assert rules[0].name == "My Rule"

    def test_deactivate_rule_returns_not_found_if_already_inactive(self):
        rule = CostingService.create_rule(
            self.tenant.id, make_rule_payload(), user_id=self.user.id
        )
        CostingService.deactivate_rule(self.tenant.id, rule.id, user_id=self.user.id)
        with pytest.raises(Conflict):
            CostingService.deactivate_rule(
                self.tenant.id, rule.id, user_id=self.user.id
            )

    def test_create_rule_requires_admin_role(self):
        employee_user = make_user("emp@example.com")
        add_member(self.tenant.id, employee_user.id, MembershipRoles.EMPLOYEE)
        with pytest.raises(Forbidden):
            CostingService.create_rule(
                self.tenant.id, make_rule_payload(), user_id=employee_user.id
            )


class CostingServiceCalculationTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        add_member(self.tenant.id, self.user.id, MembershipRoles.OWNER)
        self.employee = make_employee(self.tenant.id)

    def test_calculate_report_raises_not_found_for_wrong_tenant(self):
        approved = make_approved_report(
            self.tenant.id, self.employee.id, self.user.id
        )
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, "other")
        add_member(other_tenant.id, other_user.id, MembershipRoles.OWNER)

        with pytest.raises(NotFound):
            CostingService.calculate_report_cost(
                other_tenant.id, approved.id, user_id=other_user.id
            )

    def test_calculate_report_raises_conflict_for_wrong_status(self):
        period = TimekeepingService.create_period(
            self.tenant.id,
            PeriodIn(name="Q1 2025", start_date=date(2025, 1, 1), end_date=date(2025, 3, 31)),
            self.user.id,
        )
        report = TimekeepingService.create_time_report(
            self.tenant.id,
            period.id,
            TimeReportIn(employee_id=self.employee.id),
            self.user.id,
        )
        with pytest.raises(Conflict, match="draft"):
            CostingService.calculate_report_cost(
                self.tenant.id, report.id, user_id=self.user.id
            )

    def test_calculate_returns_correct_totals_with_no_rules(self):
        approved = make_approved_report(
            self.tenant.id, self.employee.id, self.user.id
        )
        summary = CostingService.calculate_report_cost(
            self.tenant.id, approved.id, user_id=self.user.id
        )
        assert summary.time_report_id == approved.id
        assert summary.employee_id == self.employee.id
        assert len(summary.breakdowns) == 1
        assert summary.total_base_hours == Decimal("8.00")
        # 8h * 20/h = 160
        assert summary.total_base_cost == Decimal("160.00")
        assert summary.total_cost == Decimal("160.00")
        assert summary.total_overtime_hours == Decimal("0.00")

    def test_calculate_applies_rule_when_it_matches(self):
        # Create a rule for weekdays (Monday = isoweekday 1)
        CostingService.create_rule(
            self.tenant.id,
            OvertimeRuleIn(
                name="Weekday rule",
                multiplier=Decimal("1.50"),
                priority=1,
                conditions=[{"condition_type": "day_of_week", "value": "1,2,3,4,5"}],
            ),
            user_id=self.user.id,
        )
        approved = make_approved_report(
            self.tenant.id, self.employee.id, self.user.id
        )  # entry on 2025-01-06 (Monday)

        summary = CostingService.calculate_report_cost(
            self.tenant.id, approved.id, user_id=self.user.id
        )
        assert summary.breakdowns[0].multiplier == Decimal("1.50")
        assert summary.breakdowns[0].applied_rule_name == "Weekday rule"
        # 8h * 20 * 1.5 = 240
        assert summary.total_cost == Decimal("240.00")

    def test_calculate_is_idempotent(self):
        approved = make_approved_report(
            self.tenant.id, self.employee.id, self.user.id
        )
        CostingService.calculate_report_cost(
            self.tenant.id, approved.id, user_id=self.user.id
        )
        summary = CostingService.calculate_report_cost(
            self.tenant.id, approved.id, user_id=self.user.id
        )
        # Re-calculate should overwrite, not duplicate
        assert len(summary.breakdowns) == 1
