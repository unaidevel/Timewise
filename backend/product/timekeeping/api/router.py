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
from product.timekeeping.dtos.dtos import (
    PeriodIn,
    PeriodOut,
    RejectReportRequest,
    TimeEntryIn,
    TimeEntryOut,
    TimeEntryUpdate,
    TimeReportIn,
    TimeReportOut,
    TimeReportStatusHistoryOut,
)
from product.timekeeping.orchestrators.timekeeping_orchestrator import (
    TimekeepingOrchestrator,
)
from product.timekeeping.services.timekeeping_service import TimekeepingService

router = APIRouter(prefix="/api/v1/tenants/{tenant_id}", tags=["timekeeping"])


@router.post(
    "/periods",
    response_model=PeriodOut,
    responses=responses_for(Forbidden, Conflict, UnprocessableEntity, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def create_period(
    tenant_id: int,
    payload: PeriodIn,
    current_user: RateLimitedUser,
    request: Request,
) -> PeriodOut:
    return TimekeepingOrchestrator.create_period(tenant_id, payload, current_user.id)


@router.get(
    "/periods",
    response_model=list[PeriodOut],
    responses=responses_for(TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_periods(
    tenant_id: int,
    current_user: RateLimitedUser,
    request: Request,
    status: str | None = Query(default=None),
) -> list[PeriodOut]:
    return TimekeepingService.list_periods(tenant_id, current_user.id, status)


@router.get(
    "/periods/{period_id}",
    response_model=PeriodOut,
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def get_period(
    tenant_id: int,
    period_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> PeriodOut:
    return TimekeepingService.get_period(tenant_id, period_id, current_user.id)


@router.post(
    "/periods/{period_id}/lock",
    response_model=PeriodOut,
    responses=responses_for(Forbidden, NotFound, Conflict, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def lock_period(
    tenant_id: int,
    period_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> PeriodOut:
    return TimekeepingOrchestrator.lock_period(tenant_id, period_id, current_user.id)


@router.post(
    "/periods/{period_id}/reports",
    response_model=TimeReportOut,
    responses=responses_for(NotFound, Conflict, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def create_time_report(
    tenant_id: int,
    period_id: int,
    payload: TimeReportIn,
    current_user: RateLimitedUser,
    request: Request,
) -> TimeReportOut:
    return TimekeepingOrchestrator.create_time_report(
        tenant_id, period_id, payload, current_user.id
    )


@router.get(
    "/periods/{period_id}/reports",
    response_model=list[TimeReportOut],
    responses=responses_for(Forbidden, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_time_reports_for_period(
    tenant_id: int,
    period_id: int,
    current_user: RateLimitedUser,
    request: Request,
    scope: str = Query(default="mine", pattern="^(mine|all)$"),
) -> list[TimeReportOut]:
    return TimekeepingOrchestrator.list_time_reports(
        tenant_id,
        current_user.id,
        period_id=period_id,
        scope=scope,  # type: ignore[arg-type]
    )


@router.get(
    "/reports/{report_id}",
    response_model=TimeReportOut,
    responses=responses_for(Forbidden, NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def get_time_report(
    tenant_id: int,
    report_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> TimeReportOut:
    return TimekeepingOrchestrator.get_time_report(
        tenant_id, report_id, current_user.id
    )


@router.post(
    "/reports/{report_id}/entries",
    response_model=TimeEntryOut,
    responses=responses_for(NotFound, Conflict, UnprocessableEntity, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def create_time_entry(
    tenant_id: int,
    report_id: int,
    payload: TimeEntryIn,
    current_user: RateLimitedUser,
    request: Request,
) -> TimeEntryOut:
    return TimekeepingOrchestrator.create_time_entry(
        tenant_id, report_id, payload, current_user.id
    )


@router.get(
    "/reports/{report_id}/entries",
    response_model=list[TimeEntryOut],
    responses=responses_for(Forbidden, NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_time_entries(
    tenant_id: int,
    report_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> list[TimeEntryOut]:
    return TimekeepingOrchestrator.list_time_entries(
        tenant_id, report_id, current_user.id
    )


@router.put(
    "/reports/{report_id}/entries/{entry_id}",
    response_model=TimeEntryOut,
    responses=responses_for(NotFound, Conflict, UnprocessableEntity, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def update_time_entry(
    tenant_id: int,
    report_id: int,
    entry_id: int,
    payload: TimeEntryUpdate,
    current_user: RateLimitedUser,
    request: Request,
) -> TimeEntryOut:
    return TimekeepingOrchestrator.update_time_entry(
        tenant_id, report_id, entry_id, payload, current_user.id
    )


@router.delete(
    "/reports/{report_id}/entries/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=responses_for(NotFound, Conflict, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def delete_time_entry(
    tenant_id: int,
    report_id: int,
    entry_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> None:
    TimekeepingOrchestrator.delete_time_entry(
        tenant_id, report_id, entry_id, current_user.id
    )


@router.post(
    "/reports/{report_id}/submit",
    response_model=TimeReportOut,
    responses=responses_for(
        Forbidden, NotFound, Conflict, UnprocessableEntity, TooManyRequests
    ),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def submit_time_report(
    tenant_id: int,
    report_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> TimeReportOut:
    return TimekeepingOrchestrator.submit_time_report(
        tenant_id, report_id, current_user.id
    )


@router.post(
    "/reports/{report_id}/approve",
    response_model=TimeReportOut,
    responses=responses_for(Forbidden, NotFound, Conflict, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def approve_time_report(
    tenant_id: int,
    report_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> TimeReportOut:
    return TimekeepingOrchestrator.approve_time_report(
        tenant_id, report_id, current_user.id
    )


@router.post(
    "/reports/{report_id}/reject",
    response_model=TimeReportOut,
    responses=responses_for(Forbidden, NotFound, Conflict, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def reject_time_report(
    tenant_id: int,
    report_id: int,
    payload: RejectReportRequest,
    current_user: RateLimitedUser,
    request: Request,
) -> TimeReportOut:
    return TimekeepingOrchestrator.reject_time_report(
        tenant_id, report_id, payload, current_user.id
    )


@router.post(
    "/reports/{report_id}/reopen",
    response_model=TimeReportOut,
    responses=responses_for(Forbidden, NotFound, Conflict, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def reopen_time_report(
    tenant_id: int,
    report_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> TimeReportOut:
    return TimekeepingOrchestrator.reopen_time_report(
        tenant_id, report_id, current_user.id
    )


@router.get(
    "/reports/{report_id}/history",
    response_model=list[TimeReportStatusHistoryOut],
    responses=responses_for(Forbidden, NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_report_history(
    tenant_id: int,
    report_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> list[TimeReportStatusHistoryOut]:
    return TimekeepingOrchestrator.list_report_history(
        tenant_id, report_id, current_user.id
    )
