from fastapi import APIRouter, Query, status

from infra.authz.api.dependencies import CurrentUser
from infra.common.exceptions import (
    Conflict,
    Forbidden,
    NotFound,
    UnprocessableEntity,
    responses_for,
)
from product.costing.dtos.dtos import (
    HourCostBreakdownOut,
    OvertimeRuleIn,
    OvertimeRuleOut,
    OvertimeRuleUpdate,
    ReportCostSummaryOut,
)
from product.costing.services.costing_service import CostingService

router = APIRouter(prefix="/api/v1/tenants/{tenant_id}/costing", tags=["costing"])


@router.post(
    "/rules",
    response_model=OvertimeRuleOut,
    responses=responses_for(Forbidden, Conflict, UnprocessableEntity),
    status_code=status.HTTP_201_CREATED,
)
def create_rule(
    tenant_id: int,
    payload: OvertimeRuleIn,
    current_user: CurrentUser,
) -> OvertimeRuleOut:
    return CostingService.create_rule(tenant_id, payload, user_id=current_user.id)


@router.get(
    "/rules",
    response_model=list[OvertimeRuleOut],
    responses=responses_for(Forbidden),
)
def list_rules(
    tenant_id: int,
    current_user: CurrentUser,
    active_only: bool = Query(default=False),
) -> list[OvertimeRuleOut]:
    return CostingService.list_rules(
        tenant_id, user_id=current_user.id, active_only=active_only
    )


@router.get(
    "/rules/{rule_id}",
    response_model=OvertimeRuleOut,
    responses=responses_for(Forbidden, NotFound),
)
def get_rule(
    tenant_id: int,
    rule_id: int,
    current_user: CurrentUser,
) -> OvertimeRuleOut:
    return CostingService.get_rule(tenant_id, rule_id, user_id=current_user.id)


@router.put(
    "/rules/{rule_id}",
    response_model=OvertimeRuleOut,
    responses=responses_for(Forbidden, NotFound, Conflict, UnprocessableEntity),
)
def update_rule(
    tenant_id: int,
    rule_id: int,
    payload: OvertimeRuleUpdate,
    current_user: CurrentUser,
) -> OvertimeRuleOut:
    return CostingService.update_rule(
        tenant_id, rule_id, payload, user_id=current_user.id
    )


@router.delete(
    "/rules/{rule_id}",
    response_model=OvertimeRuleOut,
    responses=responses_for(Forbidden, NotFound, Conflict),
)
def deactivate_rule(
    tenant_id: int,
    rule_id: int,
    current_user: CurrentUser,
) -> OvertimeRuleOut:
    return CostingService.deactivate_rule(tenant_id, rule_id, user_id=current_user.id)


@router.post(
    "/reports/{report_id}/calculate",
    response_model=ReportCostSummaryOut,
    responses=responses_for(Forbidden, NotFound, Conflict, UnprocessableEntity),
)
def calculate_report_cost(
    tenant_id: int,
    report_id: int,
    current_user: CurrentUser,
) -> ReportCostSummaryOut:
    return CostingService.calculate_report_cost(
        tenant_id, report_id, user_id=current_user.id
    )


@router.get(
    "/reports/{report_id}/calculations",
    response_model=list[HourCostBreakdownOut],
    responses=responses_for(Forbidden, NotFound),
)
def list_report_calculations(
    tenant_id: int,
    report_id: int,
    current_user: CurrentUser,
) -> list[HourCostBreakdownOut]:
    return CostingService.list_report_calculations(
        tenant_id, report_id, user_id=current_user.id
    )
