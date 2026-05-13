from django.db import transaction

from infra.tenants.decorators import only_admin, only_manager
from product.costing.dtos.dtos import (
    OvertimeRuleIn,
    OvertimeRuleOut,
    OvertimeRuleUpdate,
    ReportCostSummaryOut,
)
from product.costing.entities.costing_entities import (
    OvertimeRuleEntity,
    OvertimeRuleUpdateEntity,
)
from product.costing.services.costing_service import CostingService
from shared.audit.dtos.dtos import AuditEventIn
from shared.audit.services.audit_service import AuditService
from shared.audit.utils import AUDITED_FAILURES, AuditOutcome, record_failure


class CostingOrchestrator:
    @only_admin
    @staticmethod
    def create_rule(
        tenant_id: int,
        payload: OvertimeRuleIn,
        user_id: int,
    ) -> OvertimeRuleOut:
        entity = OvertimeRuleEntity(**payload.model_dump(exclude={"conditions"}))
        conditions = [
            {"condition_type": c.condition_type, "value": c.value}
            for c in payload.conditions
        ]
        try:
            with transaction.atomic():
                rule = CostingService.create_rule(
                    tenant_id, entity, conditions, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="overtime_rule.created",
                        resource_type="OvertimeRule",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=rule.id,
                        metadata={
                            "name": rule.name,
                            "multiplier": str(rule.multiplier),
                            "priority": rule.priority,
                        },
                    ),
                    user_id,
                )
                return rule
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="overtime_rule.created",
                resource_type="OvertimeRule",
                resource_id=None,
                metadata={"name": entity.name},
                exc=exc,
            )
            raise

    @only_admin
    @staticmethod
    def update_rule(
        tenant_id: int,
        rule_id: int,
        payload: OvertimeRuleUpdate,
        user_id: int,
    ) -> OvertimeRuleOut:
        entity = OvertimeRuleUpdateEntity(
            rule_id=rule_id, **payload.model_dump(exclude={"conditions"})
        )
        conditions = [
            {"condition_type": c.condition_type, "value": c.value}
            for c in payload.conditions
        ]
        try:
            with transaction.atomic():
                rule = CostingService.update_rule(
                    tenant_id, entity, conditions, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="overtime_rule.updated",
                        resource_type="OvertimeRule",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=rule.id,
                        metadata={
                            "name": rule.name,
                            "multiplier": str(rule.multiplier),
                            "priority": rule.priority,
                        },
                    ),
                    user_id,
                )
                return rule
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="overtime_rule.updated",
                resource_type="OvertimeRule",
                resource_id=rule_id,
                metadata={"name": entity.name},
                exc=exc,
            )
            raise

    @only_admin
    @staticmethod
    def deactivate_rule(
        tenant_id: int,
        rule_id: int,
        user_id: int,
    ) -> OvertimeRuleOut:
        try:
            with transaction.atomic():
                rule = CostingService.deactivate_rule(tenant_id, rule_id, user_id)
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="overtime_rule.deactivated",
                        resource_type="OvertimeRule",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=rule.id,
                    ),
                    user_id,
                )
                return rule
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="overtime_rule.deactivated",
                resource_type="OvertimeRule",
                resource_id=rule_id,
                metadata={},
                exc=exc,
            )
            raise

    @only_manager
    @staticmethod
    def calculate_report_cost(
        tenant_id: int,
        report_id: int,
        user_id: int,
    ) -> ReportCostSummaryOut:
        try:
            with transaction.atomic():
                summary = CostingService.calculate_report_cost(
                    tenant_id, report_id, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="report_cost.calculated",
                        resource_type="TimeReport",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=report_id,
                        metadata={
                            "total_cost": str(summary.total_cost),
                            "total_base_hours": str(summary.total_base_hours),
                            "total_overtime_hours": str(summary.total_overtime_hours),
                        },
                    ),
                    user_id,
                )
                return summary
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="report_cost.calculated",
                resource_type="TimeReport",
                resource_id=report_id,
                metadata={},
                exc=exc,
            )
            raise
