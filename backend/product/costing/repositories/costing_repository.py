from decimal import Decimal

from product.costing.dtos.dtos import (
    HourCostBreakdownOut,
    OvertimeRuleOut,
)
from product.costing.dtos.mappers.mappers import overtime_rule_to_dto
from product.costing.entities.costing_entities import (
    OvertimeRuleEntity,
    OvertimeRuleUpdateEntity,
)
from product.costing.models import (
    CostCalculationModel,
    OvertimeRuleModel,
    RuleConditionModel,
)
from product.timekeeping.dtos.dtos import TimeEntryOut, TimeReportOut
from product.timekeeping.models import TimeEntryModel, TimeReportModel
from product.workforce.models import EmployeeRoleModel


class CostingRepository:
    @staticmethod
    def create_rule(
        entity: OvertimeRuleEntity,
        tenant_id: int,
        created_by_id: int | None = None,
    ) -> OvertimeRuleModel:
        if not isinstance(entity, OvertimeRuleEntity):
            raise TypeError(f"Expected OvertimeRuleEntity, got {type(entity).__name__}")
        return OvertimeRuleModel.objects.create(
            tenant_id=tenant_id,
            name=entity.name,
            multiplier=entity.multiplier,
            priority=entity.priority,
            created_by_id=created_by_id,
        )

    @staticmethod
    def bulk_create_conditions(rule_id: int, conditions: list[dict]) -> None:
        RuleConditionModel.objects.bulk_create(
            [
                RuleConditionModel(
                    rule_id=rule_id,
                    condition_type=c["condition_type"],
                    value=c["value"],
                )
                for c in conditions
            ]
        )

    @staticmethod
    def get_rule_with_conditions(rule_id: int) -> OvertimeRuleOut:
        model = OvertimeRuleModel.objects.prefetch_related("conditions").get(id=rule_id)
        return overtime_rule_to_dto(model)

    @staticmethod
    def get_rule_by_id(rule_id: int) -> OvertimeRuleOut | None:
        model = (
            OvertimeRuleModel.objects.prefetch_related("conditions")
            .filter(id=rule_id)
            .first()
        )
        return overtime_rule_to_dto(model) if model else None

    @staticmethod
    def find_rule_by_name(tenant_id: int, name: str) -> OvertimeRuleOut | None:
        model = (
            OvertimeRuleModel.objects.prefetch_related("conditions")
            .filter(tenant_id=tenant_id, name__iexact=name)
            .first()
        )
        return overtime_rule_to_dto(model) if model else None

    @staticmethod
    def list_rules(
        tenant_id: int,
        active_only: bool = False,
    ) -> list[OvertimeRuleOut]:
        qs = OvertimeRuleModel.objects.prefetch_related("conditions").filter(
            tenant_id=tenant_id
        )
        if active_only:
            qs = qs.filter(is_active=True)
        return [overtime_rule_to_dto(m) for m in qs.order_by("-priority", "name")]

    @staticmethod
    def update_rule(
        entity: OvertimeRuleUpdateEntity,
        updated_by_id: int | None = None,
    ) -> None:
        if not isinstance(entity, OvertimeRuleUpdateEntity):
            raise TypeError(
                f"Expected OvertimeRuleUpdateEntity, got {type(entity).__name__}"
            )
        rule = OvertimeRuleModel(
            id=entity.rule_id,
            name=entity.name,
            multiplier=entity.multiplier,
            priority=entity.priority,
            updated_by_id=updated_by_id,
        )
        rule.save(
            update_fields=[
                "name",
                "multiplier",
                "priority",
                "updated_by_id",
                "updated_at",
            ]
        )

    @staticmethod
    def delete_conditions_for_rule(rule_id: int) -> None:
        RuleConditionModel.objects.filter(rule_id=rule_id).delete()

    @staticmethod
    def deactivate_rule(
        rule_id: int,
        updated_by_id: int | None = None,
    ) -> OvertimeRuleOut | None:
        rows = OvertimeRuleModel.objects.filter(id=rule_id, is_active=True).update(
            is_active=False, updated_by_id=updated_by_id
        )
        if rows == 0:
            return None
        model = OvertimeRuleModel.objects.prefetch_related("conditions").get(id=rule_id)
        return overtime_rule_to_dto(model)

    @staticmethod
    def get_employee_hourly_rate(employee_id: int) -> Decimal | None:
        assignment = EmployeeRoleModel.objects.filter(
            employee_id=employee_id, left_at__isnull=True
        ).first()
        return assignment.hourly_rate if assignment else None

    @staticmethod
    def get_time_report(report_id: int) -> TimeReportOut | None:
        model = TimeReportModel.objects.filter(id=report_id).first()
        return TimeReportOut.model_validate(model) if model else None

    @staticmethod
    def list_time_entries_for_report(report_id: int) -> list[TimeEntryOut]:
        return [
            TimeEntryOut.model_validate(m)
            for m in TimeEntryModel.objects.filter(report_id=report_id).order_by(
                "date", "id"
            )
        ]

    @staticmethod
    def delete_calculations_for_report(report_id: int) -> None:
        CostCalculationModel.objects.filter(time_report_id=report_id).delete()

    @staticmethod
    def save_calculations(
        calculations: list[dict],
        report_id: int,
        tenant_id: int,
        calculated_by_id: int | None = None,
    ) -> list[HourCostBreakdownOut]:
        models = CostCalculationModel.objects.bulk_create(
            [
                CostCalculationModel(
                    tenant_id=tenant_id,
                    time_report_id=report_id,
                    time_entry_id=c["time_entry_id"],
                    employee_id=c["employee_id"],
                    applied_rule_name=c["applied_rule_name"],
                    multiplier=c["multiplier"],
                    base_hours=c["base_hours"],
                    overtime_hours=c["overtime_hours"],
                    base_cost=c["base_cost"],
                    total_cost=c["total_cost"],
                    calculated_by_id=calculated_by_id,
                )
                for c in calculations
            ]
        )
        return [HourCostBreakdownOut.model_validate(m) for m in models]

    @staticmethod
    def list_calculations_for_report(report_id: int) -> list[HourCostBreakdownOut]:
        return [
            HourCostBreakdownOut.model_validate(m)
            for m in CostCalculationModel.objects.filter(
                time_report_id=report_id
            ).order_by("id")
        ]
