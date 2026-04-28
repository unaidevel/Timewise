from fastapi import APIRouter, status

from infra.authz.api.dependencies import CurrentUser
from infra.common.exceptions import (
    Conflict,
    Forbidden,
    NotFound,
    UnprocessableEntity,
    responses_for,
)
from product.approvals.dtos.dtos import (
    RejectApprovalRequest,
    ReportApprovalEventResponse,
    ReportApprovalResponse,
)
from product.approvals.orchestrators.approvals_orchestrator import (
    ApprovalsOrchestrator,
)
from product.approvals.services.approvals_service import ApprovalsService

router = APIRouter(prefix="/api/v1/tenants/{tenant_id}", tags=["approvals"])


@router.post(
    "/reports/{report_id}/submit",
    response_model=ReportApprovalResponse,
    responses=responses_for(Forbidden, NotFound, Conflict),
    status_code=status.HTTP_201_CREATED,
)
def submit_report_for_approval(
    tenant_id: int,
    report_id: int,
    current_user: CurrentUser,
) -> ReportApprovalResponse:
    return ApprovalsOrchestrator.submit_report_for_approval(
        tenant_id, report_id, current_user.id
    )


@router.post(
    "/approvals/{approval_id}/approve",
    response_model=ReportApprovalResponse,
    responses=responses_for(Forbidden, NotFound, Conflict),
)
def approve_report(
    tenant_id: int,
    approval_id: int,
    current_user: CurrentUser,
) -> ReportApprovalResponse:
    return ApprovalsOrchestrator.approve_report(tenant_id, approval_id, current_user.id)


@router.post(
    "/approvals/{approval_id}/reject",
    response_model=ReportApprovalResponse,
    responses=responses_for(Forbidden, NotFound, Conflict, UnprocessableEntity),
)
def reject_report(
    tenant_id: int,
    approval_id: int,
    payload: RejectApprovalRequest,
    current_user: CurrentUser,
) -> ReportApprovalResponse:
    return ApprovalsOrchestrator.reject_report(
        tenant_id, approval_id, payload, current_user.id
    )


@router.get(
    "/approvals",
    response_model=list[ReportApprovalResponse],
    responses=responses_for(Forbidden, NotFound),
)
def list_approvals(
    tenant_id: int,
    current_user: CurrentUser,
    status: str | None = None,
) -> list[ReportApprovalResponse]:
    return ApprovalsService.list_approvals(tenant_id, current_user.id, status)


@router.get(
    "/approvals/{approval_id}",
    response_model=ReportApprovalResponse,
    responses=responses_for(Forbidden, NotFound),
)
def get_approval(
    tenant_id: int,
    approval_id: int,
    current_user: CurrentUser,
) -> ReportApprovalResponse:
    return ApprovalsService.get_approval(tenant_id, approval_id, current_user.id)


@router.get(
    "/approvals/{approval_id}/events",
    response_model=list[ReportApprovalEventResponse],
    responses=responses_for(Forbidden, NotFound),
)
def list_approval_events(
    tenant_id: int,
    approval_id: int,
    current_user: CurrentUser,
) -> list[ReportApprovalEventResponse]:
    return ApprovalsService.list_approval_events(
        tenant_id, approval_id, current_user.id
    )
