from decimal import Decimal

from django.db import transaction

from infra.common.exceptions import Conflict, NotFound, UnprocessableEntity
from infra.tenants.decorators import any_employee, only_admin, only_manager
from product.common.classes import TimeReportStatus
from product.costing.dtos.dtos import (
    OvertimeRuleOut,
    ReportCostSummaryOut,
)
from product.costing.entities.costing_entities import (
    OvertimeRuleEntity,
    OvertimeRuleUpdateEntity,
)
from product.costing.repositories.costing_repository import CostingRepository
from product.costing.utils.rules_evaluator import (
    ConditionSpec,
    EntryContext,
    RulesEvaluator,
    RuleSpec,
)

_CALCULABLE_STATUSES = {TimeReportStatus.APPROVED, TimeReportStatus.LOCKED}
_evaluator = RulesEvaluator()


class CostingService:
    @only_admin
    @staticmethod
    def create_rule(
        tenant_id: int,
        entity: OvertimeRuleEntity,
        conditions: list[dict],
        user_id: int,
    ) -> OvertimeRuleOut:
        existing = CostingRepository.find_rule_by_name(tenant_id, entity.name)
        if existing:
            raise Conflict(
                f"An overtime rule named '{existing.name}' already exists in this tenant."
            )
        with transaction.atomic():
            rule_model = CostingRepository.create_rule(
                entity, tenant_id, created_by_id=user_id
            )
            CostingRepository.bulk_create_conditions(rule_model.id, conditions)
            return CostingRepository.get_rule_with_conditions(rule_model.id)

    @any_employee
    @staticmethod
    def get_rule(tenant_id: int, rule_id: int, user_id: int) -> OvertimeRuleOut:
        rule = CostingRepository.get_rule_by_id(rule_id)
        if not rule or rule.tenant_id != tenant_id:
            raise NotFound(f"Overtime rule {rule_id} not found.")
        return rule

    @any_employee
    @staticmethod
    def list_rules(
        tenant_id: int,
        user_id: int,
        active_only: bool = False,
    ) -> list[OvertimeRuleOut]:
        return CostingRepository.list_rules(tenant_id, active_only=active_only)

    @only_admin
    @staticmethod
    def update_rule(
        tenant_id: int,
        entity: OvertimeRuleUpdateEntity,
        conditions: list[dict],
        user_id: int,
    ) -> OvertimeRuleOut:
        rule = CostingRepository.get_rule_by_id(entity.rule_id)
        if not rule or rule.tenant_id != tenant_id:
            raise NotFound(f"Overtime rule {entity.rule_id} not found.")
        duplicate = CostingRepository.find_rule_by_name(tenant_id, entity.name)
        if duplicate and duplicate.id != entity.rule_id:
            raise Conflict(
                f"An overtime rule named '{entity.name}' already exists in this tenant."
            )
        with transaction.atomic():
            CostingRepository.update_rule(entity, updated_by_id=user_id)
            CostingRepository.delete_conditions_for_rule(entity.rule_id)
            CostingRepository.bulk_create_conditions(entity.rule_id, conditions)
            return CostingRepository.get_rule_with_conditions(entity.rule_id)

    @only_admin
    @staticmethod
    def deactivate_rule(
        tenant_id: int,
        rule_id: int,
        user_id: int,
    ) -> OvertimeRuleOut:
        rule = CostingRepository.get_rule_by_id(rule_id)
        if not rule or rule.tenant_id != tenant_id:
            raise NotFound(f"Overtime rule {rule_id} not found.")
        result = CostingRepository.deactivate_rule(rule_id, updated_by_id=user_id)
        if not result:
            raise Conflict(f"Overtime rule {rule_id} is already inactive.")
        return result

    @only_manager
    @staticmethod
    def calculate_report_cost(
        tenant_id: int,
        report_id: int,
        user_id: int,
    ) -> ReportCostSummaryOut:
        report = CostingRepository.get_time_report(report_id)
        if not report or report.tenant_id != tenant_id:
            raise NotFound(f"Time report {report_id} not found.")
        if report.status not in _CALCULABLE_STATUSES:
            raise Conflict(
                f"Cannot calculate costs for a report in status '{report.status}'. "
                "Report must be approved or locked."
            )

        hourly_rate = CostingRepository.get_employee_hourly_rate(report.employee_id)
        if hourly_rate is None:
            raise UnprocessableEntity(
                f"Employee {report.employee_id} has no active role assignment with a hourly rate."
            )

        active_rules = CostingRepository.list_rules(tenant_id, active_only=True)
        rule_specs = [
            RuleSpec(
                name=r.name,
                multiplier=r.multiplier,
                priority=r.priority,
                conditions=[
                    ConditionSpec(condition_type=c.condition_type, value=c.value)
                    for c in r.conditions
                ],
            )
            for r in active_rules
        ]

        entries = CostingRepository.list_time_entries_for_report(report_id)

        # Compute weekly_hours_so_far per entry (accumulated within each ISO week)
        weekly_accum: dict[tuple, Decimal] = {}
        entry_contexts: list[EntryContext] = []
        for entry in entries:
            week_key = (entry.date.isocalendar().year, entry.date.isocalendar().week)
            accumulated = weekly_accum.get(week_key, Decimal("0.00"))
            weekly_accum[week_key] = accumulated + entry.hours
            entry_contexts.append(
                EntryContext(
                    entry_id=entry.id,
                    date=entry.date,
                    hours=entry.hours,
                    start_time=entry.start_time,
                    end_time=entry.end_time,
                    weekly_hours_so_far=weekly_accum[week_key],
                )
            )

        breakdowns = [
            _evaluator.evaluate(ctx, hourly_rate, rule_specs, holidays=set())
            for ctx in entry_contexts
        ]

        calculations = [
            {
                "time_entry_id": bd.entry_id,
                "employee_id": report.employee_id,
                "applied_rule_name": bd.applied_rule_name,
                "multiplier": bd.multiplier,
                "base_hours": bd.base_hours,
                "overtime_hours": bd.overtime_hours,
                "base_cost": bd.base_cost,
                "total_cost": bd.total_cost,
            }
            for bd in breakdowns
        ]

        with transaction.atomic():
            CostingRepository.delete_calculations_for_report(report_id)
            saved = CostingRepository.save_calculations(
                calculations,
                report_id=report_id,
                tenant_id=tenant_id,
                calculated_by_id=user_id,
            )

        total_base_hours = sum((b.base_hours for b in saved), Decimal("0.00"))
        total_overtime_hours = sum((b.overtime_hours for b in saved), Decimal("0.00"))
        total_base_cost = sum((b.base_cost for b in saved), Decimal("0.00"))
        total_cost = sum((b.total_cost for b in saved), Decimal("0.00"))

        return ReportCostSummaryOut(
            time_report_id=report_id,
            employee_id=report.employee_id,
            total_base_hours=total_base_hours,
            total_overtime_hours=total_overtime_hours,
            total_base_cost=total_base_cost,
            total_cost=total_cost,
            breakdowns=saved,
        )

    @any_employee
    @staticmethod
    def list_report_calculations(
        tenant_id: int,
        report_id: int,
        user_id: int,
    ) -> list:
        report = CostingRepository.get_time_report(report_id)
        if not report or report.tenant_id != tenant_id:
            raise NotFound(f"Time report {report_id} not found.")
        return CostingRepository.list_calculations_for_report(report_id)
