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
from product.approvals.dtos.dtos import (
    ApprovalEventOut,
    ApprovalOut,
    RejectApprovalIn,
)
from product.approvals.orchestrators.approvals_orchestrator import (
    ApprovalsOrchestrator,
)

router = APIRouter(prefix="/api/v1/tenants/{tenant_id}", tags=["approvals"])


@router.post(
    "/reports/{report_id}/submit",
    response_model=ApprovalOut,
    responses=responses_for(Forbidden, NotFound, Conflict, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def submit_report_for_approval(
    tenant_id: int,
    report_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> ApprovalOut:
    """
    Submits a draft time report into the approval workflow, creating a pending Approval row.
    Returns ApprovalOut with HTTP 201 describing the new approval and its initial state.
    On error returns 403 (not the report owner), 404 (report missing), 409 (already submitted), or 429.
    Transitions the underlying TimeReport from draft to pending_approval atomically.
    """
    return ApprovalsOrchestrator.submit_report_for_approval(
        tenant_id, report_id, current_user.id
    )


@router.post(
    "/approvals/{approval_id}/approve",
    response_model=ApprovalOut,
    responses=responses_for(Forbidden, NotFound, Conflict, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def approve_report(
    tenant_id: int,
    approval_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> ApprovalOut:
    """
    Marks the approval as approved by the caller (must be the assigned approver).
    Returns ApprovalOut reflecting the approved state and decision timestamp.
    On error returns 403 (caller not the approver), 404, 409 (already decided), or 429.
    Also flips the linked TimeReport to approved and writes an ApprovalEvent for audit.
    """
    return ApprovalsOrchestrator.approve_report(tenant_id, approval_id, current_user.id)


@router.post(
    "/approvals/{approval_id}/reject",
    response_model=ApprovalOut,
    responses=responses_for(
        Forbidden, NotFound, Conflict, UnprocessableEntity, TooManyRequests
    ),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def reject_report(
    tenant_id: int,
    approval_id: int,
    payload: RejectApprovalIn,
    current_user: RateLimitedUser,
    request: Request,
) -> ApprovalOut:
    """
    Rejects the approval and records the required rejection reason from the payload.
    Returns ApprovalOut with the rejected state and the stored reason.
    On error returns 403, 404, 409 (already decided), 422 (reason missing/too short), or 429.
    Flips the linked TimeReport back to rejected and emits an ApprovalEvent for audit.
    """
    return ApprovalsOrchestrator.reject_report(
        tenant_id, approval_id, payload, current_user.id
    )


@router.get(
    "/approvals",
    response_model=list[ApprovalOut],
    responses=responses_for(Forbidden, NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_approvals(
    tenant_id: int,
    current_user: RateLimitedUser,
    request: Request,
    status: str | None = None,
    scope: str = Query(default="mine", pattern="^(mine|all)$"),
) -> list[ApprovalOut]:
    """
    Lists approvals in the tenant filtered by optional status and a scope of mine|all.
    Returns list[ApprovalOut]; scope=mine restricts to approvals assigned to the caller.
    On error returns 403 (scope=all without permission), 404, or 429 (rate limit).
    scope=all is intended for managers/admins; non-privileged callers are forced to mine.
    """
    return ApprovalsOrchestrator.list_approvals(
        tenant_id,
        current_user.id,
        status,
        scope,
    )


@router.get(
    "/approvals/{approval_id}",
    response_model=ApprovalOut,
    responses=responses_for(Forbidden, NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def get_approval(
    tenant_id: int,
    approval_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> ApprovalOut:
    """
    Fetches a single approval by id, scoped to the tenant and visible to the caller.
    Returns ApprovalOut with the approval's current state, approver, and decision data.
    On error returns 403 (caller can neither approve nor own the report), 404, or 429.
    Visibility check covers both report-owners and the assigned approver chain.
    """
    return ApprovalsOrchestrator.get_approval(tenant_id, approval_id, current_user.id)


@router.get(
    "/approvals/{approval_id}/events",
    response_model=list[ApprovalEventOut],
    responses=responses_for(Forbidden, NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_approval_events(
    tenant_id: int,
    approval_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> list[ApprovalEventOut]:
    """
    Lists the chronological history of state transitions for a single approval.
    Returns list[ApprovalEventOut] ordered oldest-first with actor, action, and timestamp.
    On error returns 403 (caller cannot view this approval), 404, or 429 (rate limit).
    Read-only audit trail — there is no endpoint to mutate or delete individual events.
    """
    return ApprovalsOrchestrator.list_approval_events(
        tenant_id, approval_id, current_user.id
    )
