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
from infra.common.classes import MembershipRoles
from infra.tenants.api import router as tenants_router
from infra.tenants.dtos.dtos import TenantIn
from infra.tenants.entities.tenant_entities import TenantMembershipEntity
from infra.tenants.services.tenants_service import TenantService
from product.costing.api import router as costing_router
from product.costing.dtos.dtos import OvertimeRuleIn, OvertimeRuleUpdate
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


class CostingApiTests(TestCase):
    def _authenticate_user(self, *, email: str, full_name: str):
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
        self.user = self._authenticate_user(
            email="owner@example.com", full_name="Owner"
        )
        self.tenant = tenants_router.create(
            TenantIn(name="Acme Corp", slug="acme"),
            current_user=self.user,
            request=build_request(),
        )
        dept = workforce_router.create_department(
            self.tenant.id,
            DepartmentIn(name="Engineering"),
            self.user,
            request=build_request(),
        )
        role = workforce_router.create_role(
            self.tenant.id,
            RoleIn(name="Developer"),
            self.user,
            request=build_request(),
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
            request=build_request(),
        )

    def _make_rule_payload(self, name: str = "Weekend rule") -> OvertimeRuleIn:
        return OvertimeRuleIn(
            name=name,
            multiplier=Decimal("1.50"),
            priority=1,
            conditions=[{"condition_type": "day_of_week", "value": "6,7"}],
        )

    def _create_approved_report(self):
        period = timekeeping_router.create_period(
            self.tenant.id,
            PeriodIn(
                name="Q1 2025", start_date=date(2025, 1, 1), end_date=date(2025, 3, 31)
            ),
            self.user,
            request=build_request(),
        )
        report = timekeeping_router.create_time_report(
            self.tenant.id,
            period.id,
            TimeReportIn(employee_id=self.employee.id),
            self.user,
            request=build_request(),
        )
        timekeeping_router.create_time_entry(
            self.tenant.id,
            report.id,
            TimeEntryIn(date=date(2025, 1, 6), hours=Decimal("8.00")),
            self.user,
            request=build_request(),
        )
        timekeeping_router.submit_time_report(
            self.tenant.id, report.id, self.user, request=build_request()
        )
        return timekeeping_router.approve_time_report(
            self.tenant.id,
            report.id,
            self.user,
            request=build_request(),
        )

    # --- Auth ---

    def test_endpoints_require_authentication(self):
        with pytest.raises(HTTPException) as exc:
            get_current_user(None)
        assert exc.value.status_code == 401

    # --- Rules CRUD ---

    def test_create_rule_returns_rule_for_admin(self):
        rule = costing_router.create_rule(
            self.tenant.id,
            self._make_rule_payload(),
            self.user,
            request=build_request(),
        )
        assert rule.name == "Weekend rule"
        assert rule.multiplier == Decimal("1.50")
        assert rule.tenant_id == self.tenant.id
        assert len(rule.conditions) == 1
        assert rule.conditions[0].condition_type == "day_of_week"

    def test_create_rule_raises_403_for_employee_role(self):
        employee_user = self._authenticate_user(
            email="emp@example.com", full_name="Employee"
        )
        TenantService.add_membership(
            tenant_id=self.tenant.id,
            user_id=employee_user.id,
            entity=TenantMembershipEntity(role=MembershipRoles.EMPLOYEE.value),
            invited_by_id=None,
        )
        with pytest.raises(HTTPException) as exc:
            costing_router.create_rule(
                self.tenant.id,
                self._make_rule_payload(),
                employee_user,
                request=build_request(),
            )
        assert exc.value.status_code == 403

    def test_create_rule_raises_409_on_duplicate_name(self):
        costing_router.create_rule(
            self.tenant.id,
            self._make_rule_payload("Overtime"),
            self.user,
            request=build_request(),
        )
        with pytest.raises(HTTPException) as exc:
            costing_router.create_rule(
                self.tenant.id,
                self._make_rule_payload("Overtime"),
                self.user,
                request=build_request(),
            )
        assert exc.value.status_code == 409

    def test_list_rules_returns_all_tenant_rules(self):
        costing_router.create_rule(
            self.tenant.id,
            self._make_rule_payload("Rule A"),
            self.user,
            request=build_request(),
        )
        costing_router.create_rule(
            self.tenant.id,
            self._make_rule_payload("Rule B"),
            self.user,
            request=build_request(),
        )
        rules = costing_router.list_rules(
            self.tenant.id, self.user, request=build_request()
        )
        assert len(rules) == 2

    def test_list_rules_active_only_filter(self):
        rule = costing_router.create_rule(
            self.tenant.id,
            self._make_rule_payload(),
            self.user,
            request=build_request(),
        )
        costing_router.deactivate_rule(
            self.tenant.id, rule.id, self.user, request=build_request()
        )
        all_rules = costing_router.list_rules(
            self.tenant.id,
            self.user,
            active_only=False,
            request=build_request(),
        )
        active_rules = costing_router.list_rules(
            self.tenant.id,
            self.user,
            active_only=True,
            request=build_request(),
        )
        assert len(all_rules) == 1
        assert len(active_rules) == 0

    def test_get_rule_raises_404_for_missing_rule(self):
        with pytest.raises(HTTPException) as exc:
            costing_router.get_rule(
                self.tenant.id, 99999, self.user, request=build_request()
            )
        assert exc.value.status_code == 404

    def test_update_rule_changes_name_and_conditions(self):
        rule = costing_router.create_rule(
            self.tenant.id,
            self._make_rule_payload(),
            self.user,
            request=build_request(),
        )
        updated = costing_router.update_rule(
            self.tenant.id,
            rule.id,
            OvertimeRuleUpdate(
                name="Holiday rule",
                multiplier=Decimal("1.50"),
                priority=1,
                conditions=[{"condition_type": "is_holiday", "value": "true"}],
            ),
            self.user,
            request=build_request(),
        )
        assert updated.name == "Holiday rule"
        assert updated.conditions[0].condition_type == "is_holiday"

    def test_deactivate_rule_returns_rule_with_is_active_false(self):
        rule = costing_router.create_rule(
            self.tenant.id,
            self._make_rule_payload(),
            self.user,
            request=build_request(),
        )
        deactivated = costing_router.deactivate_rule(
            self.tenant.id, rule.id, self.user, request=build_request()
        )
        assert deactivated.is_active is False

    def test_deactivate_already_inactive_rule_raises_409(self):
        rule = costing_router.create_rule(
            self.tenant.id,
            self._make_rule_payload(),
            self.user,
            request=build_request(),
        )
        costing_router.deactivate_rule(
            self.tenant.id, rule.id, self.user, request=build_request()
        )
        with pytest.raises(HTTPException) as exc:
            costing_router.deactivate_rule(
                self.tenant.id, rule.id, self.user, request=build_request()
            )
        assert exc.value.status_code == 409

    # --- Calculations ---

    def test_calculate_report_returns_summary(self):
        approved = self._create_approved_report()
        summary = costing_router.calculate_report_cost(
            self.tenant.id,
            approved.id,
            self.user,
            request=build_request(),
        )
        assert summary.time_report_id == approved.id
        assert summary.employee_id == self.employee.id
        assert len(summary.breakdowns) == 1
        # 8h * 30/h = 240 with no rules applied
        assert summary.total_cost == Decimal("240.00")
        assert summary.total_overtime_hours == Decimal("0.00")

    def test_calculate_report_raises_404_for_wrong_tenant(self):
        approved = self._create_approved_report()
        other_user = self._authenticate_user(
            email="other@example.com", full_name="Other"
        )
        other_tenant = tenants_router.create(
            TenantIn(name="Other Corp", slug="other"),
            current_user=other_user,
            request=build_request(),
        )
        with pytest.raises(HTTPException) as exc:
            costing_router.calculate_report_cost(
                other_tenant.id,
                approved.id,
                other_user,
                request=build_request(),
            )
        assert exc.value.status_code == 404

    def test_list_calculations_returns_stored_breakdowns(self):
        approved = self._create_approved_report()
        costing_router.calculate_report_cost(
            self.tenant.id, approved.id, self.user, request=build_request()
        )
        calculations = costing_router.list_report_calculations(
            self.tenant.id,
            approved.id,
            self.user,
            request=build_request(),
        )
        assert len(calculations) == 1
        assert calculations[0].time_entry_id is not None

    def test_list_calculations_raises_404_for_missing_report(self):
        with pytest.raises(HTTPException) as exc:
            costing_router.list_report_calculations(
                self.tenant.id, 99999, self.user, request=build_request()
            )
        assert exc.value.status_code == 404
