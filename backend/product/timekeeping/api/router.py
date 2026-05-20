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
    """
    Creates a new timekeeping period (start/end window) for the tenant.
    Returns PeriodOut with HTTP 201 carrying the persisted period.
    On error returns 403 (caller cannot manage periods), 409 (date range overlap), 422, or 429.
    Date range validation blocks overlap with existing open periods in the same tenant.
    """
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
    """
    Lists timekeeping periods for the tenant, optionally filtered by status (open/locked).
    Returns list[PeriodOut] ordered by start_date descending.
    On error returns 429 (rate limit); membership is enforced by the dependency.
    Visible to any tenant member; status filter is loose (unknown values yield an empty list).
    """
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
    """
    Fetches a single timekeeping period by id, scoped to the tenant.
    Returns PeriodOut with the period's window, status, and lock metadata.
    On error returns 404 (period missing in tenant) or 429 (rate limit).
    Cross-tenant fetch is denied even with the correct id.
    """
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
    """
    Locks the period so no further reports or entries can be created/edited within it.
    Returns PeriodOut reflecting the locked state and the lock timestamp.
    On error returns 403 (caller cannot manage periods), 404, 409 (already locked), or 429.
    Pending approvals on existing reports remain actionable; only new mutations are blocked.
    """
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
    """
    Creates a new draft TimeReport for an employee inside the given period.
    Returns TimeReportOut with HTTP 201 describing the new report (initial status = draft).
    On error returns 404 (period/employee missing), 409 (report already exists), or 429.
    One report per (employee, period) is enforced via a unique constraint.
    """
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
    """
    Lists time reports under a period; scope=mine returns the caller's only, scope=all returns every report.
    Returns list[TimeReportOut] ordered by created_at descending.
    On error returns 403 (scope=all without manager rights) or 429 (rate limit).
    scope=all is restricted to managers/admins; non-privileged callers are silently scoped to mine.
    """
    return TimekeepingOrchestrator.list_time_reports(
        tenant_id,
        current_user.id,
        period_id,
        scope,
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
    """
    Fetches a single time report by id, scoped to the tenant.
    Returns TimeReportOut with status, totals, and the linked employee/period ids.
    On error returns 403 (caller is neither owner nor approver), 404, or 429 (rate limit).
    Read access requires the caller to own the report or be in its approval chain.
    """
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
    """
    Adds a single time entry (day + hours + optional note) to a draft time report.
    Returns TimeEntryOut with HTTP 201 carrying the new entry.
    On error returns 404 (report missing), 409 (report not draft, date already used), 422, or 429.
    Only draft reports accept new entries; submitted/approved/rejected reports are read-only here.
    """
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
    """
    Lists all time entries belonging to the given time report.
    Returns list[TimeEntryOut] ordered by entry date ascending.
    On error returns 403 (caller cannot view the report), 404, or 429 (rate limit).
    Visibility mirrors get_time_report — owner or approval-chain only.
    """
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
    """
    Updates a time entry's hours, date, and/or note on a still-editable report.
    Returns TimeEntryOut with the post-update entry.
    On error returns 404, 409 (parent report not draft), 422 (invalid hours), or 429.
    Hours and date validation runs the same checks as creation.
    """
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
    """
    Hard-deletes a time entry from a draft time report.
    Returns HTTP 204 with no body on success.
    On error returns 404, 409 (report not draft), or 429 (rate limit).
    Deletion is final — once approved, entries can no longer be removed via this endpoint.
    """
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
    """
    Submits the draft report for approval, transitioning it to pending_approval.
    Returns TimeReportOut with the new status and creates the matching Approval row.
    On error returns 403 (caller not the owner), 404, 409 (not draft, no entries), 422, or 429.
    A status_history row is appended; downstream Approval workflow drives subsequent transitions.
    """
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
    """
    Approves a pending time report directly via the timekeeping module (mirrors Approval flow).
    Returns TimeReportOut with status flipped to approved and decision timestamp set.
    On error returns 403 (caller not an approver), 404, 409 (not pending), or 429.
    Use this as a convenience for managers; the canonical path is the /approvals/{id}/approve endpoint.
    """
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
    """
    Rejects a pending time report with a required reason, sending it back for revision.
    Returns TimeReportOut with status flipped to rejected and the stored reason.
    On error returns 403, 404, 409 (not pending), 422 (missing reason), or 429.
    The owning employee can then reopen the report to edit and resubmit.
    """
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
    """
    Returns a rejected report to draft so the owner can edit and resubmit it.
    Returns TimeReportOut with status flipped back to draft.
    On error returns 403 (not owner), 404, 409 (report not in rejected state), or 429.
    Only rejected reports are reopenable; approved/locked reports stay final.
    """
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
    """
    Lists every status transition recorded for the time report (submit, approve, reject, reopen).
    Returns list[TimeReportStatusHistoryOut] ordered oldest-first with actor and timestamp.
    On error returns 403 (caller cannot view the report), 404, or 429 (rate limit).
    Read-only audit trail; history is appended automatically by the orchestrator on each transition.
    """
    return TimekeepingOrchestrator.list_report_history(
        tenant_id, report_id, current_user.id
    )
