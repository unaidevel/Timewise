from decimal import Decimal

from django.db import transaction

from product.costing.dtos.dtos import (
    HourCostBreakdownOut,
    OvertimeRuleOut,
    RuleConditionOut,
)
from product.costing.entities.costing_entities import OvertimeRuleEntity
from product.costing.models import (
    CostCalculationModel,
    OvertimeRuleModel,
    RuleConditionModel,
)
from product.timekeeping.dtos.dtos import TimeEntryOut, TimeReportOut
from product.timekeeping.models import TimeEntryModel, TimeReportModel
from product.workforce.models import EmployeeRoleModel


def _rule_to_dto(model: OvertimeRuleModel) -> OvertimeRuleOut:
    conditions = [RuleConditionOut.model_validate(c) for c in model.conditions.all()]
    return OvertimeRuleOut(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        multiplier=model.multiplier,
        priority=model.priority,
        is_active=model.is_active,
        conditions=conditions,
        created_by_id=model.created_by_id,
        updated_by_id=model.updated_by_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class CostingRepository:
    # -------------------------------------------------------------------------
    # Overtime rules
    # -------------------------------------------------------------------------

    @staticmethod
    def create_rule(
        entity: OvertimeRuleEntity,
        conditions: list[dict],
        tenant_id: int,
        created_by_id: int | None = None,
    ) -> OvertimeRuleOut:
        if not isinstance(entity, OvertimeRuleEntity):
            raise TypeError(f"Expected OvertimeRuleEntity, got {type(entity).__name__}")
        with transaction.atomic():
            model = OvertimeRuleModel.objects.create(
                tenant_id=tenant_id,
                name=entity.name,
                multiplier=entity.multiplier,
                priority=entity.priority,
                created_by_id=created_by_id,
            )
            RuleConditionModel.objects.bulk_create(
                [
                    RuleConditionModel(
                        rule=model,
                        condition_type=c["condition_type"],
                        value=c["value"],
                    )
                    for c in conditions
                ]
            )
        model.refresh_from_db()
        model.conditions.all()  # warm the related manager
        return _rule_to_dto(model)

    @staticmethod
    def get_rule_by_id(rule_id: int) -> OvertimeRuleOut | None:
        model = (
            OvertimeRuleModel.objects.prefetch_related("conditions")
            .filter(id=rule_id)
            .first()
        )
        return _rule_to_dto(model) if model else None

    @staticmethod
    def find_rule_by_name(tenant_id: int, name: str) -> OvertimeRuleOut | None:
        model = (
            OvertimeRuleModel.objects.prefetch_related("conditions")
            .filter(tenant_id=tenant_id, name__iexact=name)
            .first()
        )
        return _rule_to_dto(model) if model else None

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
        return [_rule_to_dto(m) for m in qs.order_by("-priority", "name")]

    @staticmethod
    def update_rule(
        rule_id: int,
        name: str | None = None,
        multiplier: Decimal | None = None,
        priority: int | None = None,
        conditions: list[dict] | None = None,
        updated_by_id: int | None = None,
    ) -> OvertimeRuleOut | None:
        with transaction.atomic():
            update_fields: dict = {}
            if name is not None:
                update_fields["name"] = name
            if multiplier is not None:
                update_fields["multiplier"] = multiplier
            if priority is not None:
                update_fields["priority"] = priority
            if updated_by_id is not None:
                update_fields["updated_by_id"] = updated_by_id

            if update_fields:
                rows = OvertimeRuleModel.objects.filter(id=rule_id).update(
                    **update_fields
                )
                if rows == 0:
                    return None

            if conditions is not None:
                RuleConditionModel.objects.filter(rule_id=rule_id).delete()
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

        model = OvertimeRuleModel.objects.prefetch_related("conditions").get(id=rule_id)
        return _rule_to_dto(model)

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
        return _rule_to_dto(model)

    # -------------------------------------------------------------------------
    # Cross-module queries (read-only from other modules' models)
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # Cost calculations
    # -------------------------------------------------------------------------

    @staticmethod
    def save_calculations(
        calculations: list[dict],
        report_id: int,
        tenant_id: int,
        calculated_by_id: int | None = None,
    ) -> list[HourCostBreakdownOut]:
        with transaction.atomic():
            CostCalculationModel.objects.filter(time_report_id=report_id).delete()
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
