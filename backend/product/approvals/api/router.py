from fastapi import APIRouter, Request, status

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
from product.approvals.services.approvals_service import ApprovalsService

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
) -> list[ApprovalOut]:
    return ApprovalsService.list_approvals(tenant_id, current_user.id, status)


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
    return ApprovalsService.get_approval(tenant_id, approval_id, current_user.id)


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
    return ApprovalsService.list_approval_events(
        tenant_id, approval_id, current_user.id
    )
