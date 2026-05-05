from datetime import date
from decimal import Decimal

from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.services.tenants_service import TenantService
from product.common.classes import TimeReportStatus
from product.costing.entities.costing_entities import (
    OvertimeRuleEntity,
    OvertimeRuleUpdateEntity,
)
from product.costing.repositories.costing_repository import CostingRepository
from product.timekeeping.models import PeriodModel, TimeEntryModel, TimeReportModel
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


def make_rule_entity(name: str = "Weekend rule") -> OvertimeRuleEntity:
    return OvertimeRuleEntity(
        name=name,
        multiplier=Decimal("1.50"),
        priority=1,
    )


def weekend_conditions() -> list[dict]:
    return [{"condition_type": "day_of_week", "value": "6,7"}]


class CostingRepositoryRulesTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        TenantService.add_membership(
            tenant_id=self.tenant.id,
            user_id=self.user.id,
            entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
            invited_by_id=None,
        )

    def test_create_rule_persists_rule_and_conditions(self):
        entity = make_rule_entity()
        rule = CostingRepository.create_rule(
            entity,
            weekend_conditions(),
            self.tenant.id,
            created_by_id=self.user.id,
        )
        assert rule.name == "Weekend rule"
        assert rule.multiplier == Decimal("1.50")
        assert rule.priority == 1
        assert rule.tenant_id == self.tenant.id
        assert rule.is_active is True
        assert len(rule.conditions) == 1
        assert rule.conditions[0].condition_type == "day_of_week"
        assert rule.conditions[0].value == "6,7"

    def test_get_rule_by_id_returns_none_when_missing(self):
        assert CostingRepository.get_rule_by_id(99999) is None

    def test_get_rule_by_id_returns_rule_with_conditions(self):
        entity = make_rule_entity()
        created = CostingRepository.create_rule(
            entity, weekend_conditions(), self.tenant.id
        )
        fetched = CostingRepository.get_rule_by_id(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert len(fetched.conditions) == 1

    def test_find_rule_by_name_is_case_insensitive(self):
        entity = make_rule_entity("Weekend Rule")
        CostingRepository.create_rule(entity, weekend_conditions(), self.tenant.id)
        found = CostingRepository.find_rule_by_name(self.tenant.id, "weekend rule")
        assert found is not None
        assert found.name == "Weekend Rule"

    def test_list_rules_returns_only_tenant_rules(self):
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, "other")
        CostingRepository.create_rule(
            make_rule_entity("My Rule"), weekend_conditions(), self.tenant.id
        )
        CostingRepository.create_rule(
            make_rule_entity("Other Tenant Rule"), weekend_conditions(), other_tenant.id
        )
        rules = CostingRepository.list_rules(self.tenant.id)
        assert len(rules) == 1
        assert rules[0].name == "My Rule"

    def test_list_rules_ordered_by_priority_desc_then_name(self):
        CostingRepository.create_rule(
            OvertimeRuleEntity(name="A rule", multiplier=Decimal("1.50"), priority=1),
            weekend_conditions(),
            self.tenant.id,
        )
        CostingRepository.create_rule(
            OvertimeRuleEntity(name="B rule", multiplier=Decimal("1.50"), priority=5),
            weekend_conditions(),
            self.tenant.id,
        )
        rules = CostingRepository.list_rules(self.tenant.id)
        assert rules[0].priority == 5
        assert rules[1].priority == 1

    def test_list_rules_active_only_filter(self):
        active_entity = make_rule_entity("Active Rule")
        created = CostingRepository.create_rule(
            active_entity, weekend_conditions(), self.tenant.id
        )
        CostingRepository.deactivate_rule(created.id)
        all_rules = CostingRepository.list_rules(self.tenant.id)
        active_rules = CostingRepository.list_rules(self.tenant.id, active_only=True)
        assert len(all_rules) == 1
        assert len(active_rules) == 0

    def test_update_rule_replaces_conditions(self):
        entity = make_rule_entity()
        created = CostingRepository.create_rule(
            entity,
            weekend_conditions(),
            self.tenant.id,
        )
        update_entity = OvertimeRuleUpdateEntity(
            rule_id=created.id,
            name=created.name,
            multiplier=created.multiplier,
            priority=created.priority,
        )
        new_conditions = [{"condition_type": "is_holiday", "value": "true"}]
        updated = CostingRepository.update_rule(update_entity, new_conditions)
        assert len(updated.conditions) == 1
        assert updated.conditions[0].condition_type == "is_holiday"

    def test_update_rule_changes_name(self):
        entity = make_rule_entity()
        created = CostingRepository.create_rule(
            entity, weekend_conditions(), self.tenant.id
        )
        update_entity = OvertimeRuleUpdateEntity(
            rule_id=created.id,
            name="Updated Name",
            multiplier=created.multiplier,
            priority=created.priority,
        )
        updated = CostingRepository.update_rule(update_entity, weekend_conditions())
        assert updated.name == "Updated Name"
        assert len(updated.conditions) == 1
        assert updated.conditions[0].condition_type == "day_of_week"

    def test_deactivate_rule_sets_is_active_false(self):
        entity = make_rule_entity()
        created = CostingRepository.create_rule(
            entity, weekend_conditions(), self.tenant.id
        )
        deactivated = CostingRepository.deactivate_rule(created.id)
        assert deactivated is not None
        assert deactivated.is_active is False

    def test_deactivate_rule_returns_none_when_already_inactive(self):
        entity = make_rule_entity()
        created = CostingRepository.create_rule(
            entity, weekend_conditions(), self.tenant.id
        )
        CostingRepository.deactivate_rule(created.id)
        result = CostingRepository.deactivate_rule(created.id)
        assert result is None


class CostingRepositoryCalculationsTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        TenantService.add_membership(
            tenant_id=self.tenant.id,
            user_id=self.user.id,
            entity=TenantMembershipEntity(role=MembershipRoles.OWNER.value),
            invited_by_id=None,
        )
        self.employee = make_employee(self.tenant.id)

        period = PeriodModel.objects.create(
            tenant_id=self.tenant.id,
            name="Q1 2025",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )
        self.report = TimeReportModel.objects.create(
            tenant_id=self.tenant.id,
            employee_id=self.employee.id,
            period_id=period.id,
            status=TimeReportStatus.APPROVED,
        )
        self.entry = TimeEntryModel.objects.create(
            report_id=self.report.id,
            date=date(2025, 1, 6),
            hours=Decimal("8.00"),
        )

    def test_get_employee_hourly_rate_returns_rate(self):
        rate = CostingRepository.get_employee_hourly_rate(self.employee.id)
        assert rate == Decimal("25.00")

    def test_get_employee_hourly_rate_returns_none_for_unknown_employee(self):
        assert CostingRepository.get_employee_hourly_rate(99999) is None

    def test_list_time_entries_for_report_returns_entries_ordered_by_date(self):
        entries = CostingRepository.list_time_entries_for_report(self.report.id)
        assert len(entries) == 1
        assert entries[0].id == self.entry.id

    def test_save_calculations_persists_and_returns_breakdowns(self):
        calculations = [
            {
                "time_entry_id": self.entry.id,
                "employee_id": self.employee.id,
                "applied_rule_name": "",
                "multiplier": Decimal("1.00"),
                "base_hours": Decimal("8.00"),
                "overtime_hours": Decimal("0.00"),
                "base_cost": Decimal("200.00"),
                "total_cost": Decimal("200.00"),
            }
        ]
        saved = CostingRepository.save_calculations(
            calculations,
            report_id=self.report.id,
            tenant_id=self.tenant.id,
            calculated_by_id=self.user.id,
        )
        assert len(saved) == 1
        assert saved[0].time_entry_id == self.entry.id
        assert saved[0].total_cost == Decimal("200.00")

    def test_save_calculations_is_idempotent(self):
        calculations = [
            {
                "time_entry_id": self.entry.id,
                "employee_id": self.employee.id,
                "applied_rule_name": "",
                "multiplier": Decimal("1.00"),
                "base_hours": Decimal("8.00"),
                "overtime_hours": Decimal("0.00"),
                "base_cost": Decimal("200.00"),
                "total_cost": Decimal("200.00"),
            }
        ]
        CostingRepository.save_calculations(
            calculations, report_id=self.report.id, tenant_id=self.tenant.id
        )
        # Call again — should overwrite, not duplicate
        CostingRepository.save_calculations(
            calculations, report_id=self.report.id, tenant_id=self.tenant.id
        )
        listed = CostingRepository.list_calculations_for_report(self.report.id)
        assert len(listed) == 1

    def test_list_calculations_returns_empty_for_unknown_report(self):
        assert CostingRepository.list_calculations_for_report(99999) == []
