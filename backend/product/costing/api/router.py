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
    """
    Creates a new overtime/costing rule (thresholds + multipliers) for the tenant.
    Returns OvertimeRuleOut with HTTP 201 carrying the persisted rule.
    On error returns 403 (caller cannot manage rules), 409 (rule name collision), 422, or 429.
    Validates threshold ranges and multiplier sanity before persisting.
    """
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
    """
    Lists overtime rules for the tenant; active_only=true filters out deactivated rules.
    Returns list[OvertimeRuleOut]; ordered by created_at descending.
    On error returns 403 (caller cannot read rules) or 429 (rate limit).
    Deactivated rules are retained for historical cost recalculation, not hidden by default.
    """
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
    """
    Fetches a single overtime rule by id, scoped to the tenant.
    Returns OvertimeRuleOut with thresholds, multipliers, and active state.
    On error returns 403 (no read rights), 404 (rule missing in tenant), or 429.
    Cross-tenant access is denied even if the rule id is correct.
    """
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
    """
    Updates editable fields (name/thresholds/multipliers/active state) of an existing rule.
    Returns OvertimeRuleOut with the post-update rule.
    On error returns 403, 404, 409 (name collision), 422 (invalid thresholds), or 429.
    Past cost calculations are not retroactively re-applied — only new calculations use the new values.
    """
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
    """
    Soft-deletes the rule by setting its active flag to false (the row is preserved).
    Returns OvertimeRuleOut showing the rule now in its deactivated state.
    On error returns 403, 404, 409 (already inactive), or 429 (rate limit).
    Historical calculations remain referenceable; new calculations skip inactive rules.
    """
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
    """
    Runs cost calculation across all time entries on the report and persists per-hour breakdowns.
    Returns ReportCostSummaryOut with totals (regular, overtime, by-rule) for the whole report.
    On error returns 403, 404 (report missing), 409 (report not approved yet), 422, or 429.
    Recomputes from scratch on every call; safe to retry after rule changes.
    """
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
    """
    Lists every per-hour cost breakdown row stored against the report's last calculation run.
    Returns list[HourCostBreakdownOut] with rule applied, hours, multiplier, and resulting cost.
    On error returns 403, 404 (report or breakdowns missing), or 429 (rate limit).
    Empty list means the report has never been costed — invoke calculate_report_cost first.
    """
    return CostingOrchestrator.list_report_calculations(
        tenant_id, report_id, current_user.id
    )
