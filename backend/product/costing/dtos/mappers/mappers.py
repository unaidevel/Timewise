from product.costing.dtos.dtos import OvertimeRuleOut, RuleConditionOut
from product.costing.models import OvertimeRuleModel


def overtime_rule_to_dto(model: OvertimeRuleModel) -> OvertimeRuleOut:
    return OvertimeRuleOut(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        multiplier=model.multiplier,
        priority=model.priority,
        is_active=model.is_active,
        conditions=[RuleConditionOut.model_validate(c) for c in model.conditions.all()],
        created_by_id=model.created_by_id,
        updated_by_id=model.updated_by_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
