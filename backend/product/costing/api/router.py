from fastapi import APIRouter, Query, Request, status

from infra.authz.api.dependencies import RateLimitedUser
from infra.common.exceptions import (
    Conflict,
    Forbidden,
    NotFound,
    TooManyRequests,
    UnprocessableEntity,
    responses_for,
)
from infra.common.rate_limiting import USER_RATE_LIMIT, limiter, user_or_ip_key
from product.costing.dtos.dtos import (
    HourCostBreakdownOut,
    OvertimeRuleIn,
    OvertimeRuleOut,
    OvertimeRuleUpdate,
    ReportCostSummaryOut,
)
from product.costing.orchestrators.costing_orchestrator import CostingOrchestrator
from product.costing.services.costing_service import CostingService

router = APIRouter(prefix="/api/v1/tenants/{tenant_id}/costing", tags=["costing"])


@router.post(
    "/rules",
    response_model=OvertimeRuleOut,
    responses=responses_for(Forbidden, Conflict, UnprocessableEntity, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def create_rule(
    tenant_id: int,
    payload: OvertimeRuleIn,
    current_user: RateLimitedUser,
    request: Request,
) -> OvertimeRuleOut:
    return CostingOrchestrator.create_rule(tenant_id, payload, current_user.id)


@router.get(
    "/rules",
    response_model=list[OvertimeRuleOut],
    responses=responses_for(Forbidden, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_rules(
    tenant_id: int,
    current_user: RateLimitedUser,
    request: Request,
    active_only: bool = Query(default=False),
) -> list[OvertimeRuleOut]:
    return CostingService.list_rules(tenant_id, current_user.id, active_only)


@router.get(
    "/rules/{rule_id}",
    response_model=OvertimeRuleOut,
    responses=responses_for(Forbidden, NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def get_rule(
    tenant_id: int,
    rule_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> OvertimeRuleOut:
    return CostingService.get_rule(tenant_id, rule_id, current_user.id)


@router.put(
    "/rules/{rule_id}",
    response_model=OvertimeRuleOut,
    responses=responses_for(
        Forbidden, NotFound, Conflict, UnprocessableEntity, TooManyRequests
    ),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def update_rule(
    tenant_id: int,
    rule_id: int,
    payload: OvertimeRuleUpdate,
    current_user: RateLimitedUser,
    request: Request,
) -> OvertimeRuleOut:
    return CostingOrchestrator.update_rule(tenant_id, rule_id, payload, current_user.id)


@router.delete(
    "/rules/{rule_id}",
    response_model=OvertimeRuleOut,
    responses=responses_for(Forbidden, NotFound, Conflict, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def deactivate_rule(
    tenant_id: int,
    rule_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> OvertimeRuleOut:
    return CostingOrchestrator.deactivate_rule(tenant_id, rule_id, current_user.id)


@router.post(
    "/reports/{report_id}/calculate",
    response_model=ReportCostSummaryOut,
    responses=responses_for(
        Forbidden, NotFound, Conflict, UnprocessableEntity, TooManyRequests
    ),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def calculate_report_cost(
    tenant_id: int,
    report_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> ReportCostSummaryOut:
    return CostingOrchestrator.calculate_report_cost(
        tenant_id, report_id, current_user.id
    )


@router.get(
    "/reports/{report_id}/calculations",
    response_model=list[HourCostBreakdownOut],
    responses=responses_for(Forbidden, NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_report_calculations(
    tenant_id: int,
    report_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> list[HourCostBreakdownOut]:
    return CostingService.list_report_calculations(
        tenant_id, report_id, current_user.id
    )
