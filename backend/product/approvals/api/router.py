from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from infra.authz.api.dependencies import CurrentUser
from product.approvals.dtos.dtos import (
    ApprovalResponse,
    CreateApprovalRequest,
    UpdateApprovalRequest,
)
from product.approvals.dtos.mappers.approval_mapper import to_approval_response
from product.approvals.exceptions import (
    ApprovalNotFoundError,
    InvalidApprovalValueError,
)
from product.approvals.services.approvals_service import ApprovalsService

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


def _raise_http_exception(exc: Exception) -> None:
    if isinstance(exc, ApprovalNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    if isinstance(exc, InvalidApprovalValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    raise exc


@router.post(
    "",
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_approval(
    payload: CreateApprovalRequest,
    current_user: CurrentUser,
) -> ApprovalResponse:
    try:
        approval = ApprovalsService.create_approval(
            title=payload.title,
            description=payload.description,
            created_by_user_id=current_user.id,
        )
    except InvalidApprovalValueError as exc:
        _raise_http_exception(exc)

    return to_approval_response(approval)


@router.get("", response_model=list[ApprovalResponse])
def list_approvals(current_user: CurrentUser) -> list[ApprovalResponse]:
    approvals = ApprovalsService.list_approvals(current_user.id)
    return [to_approval_response(approval) for approval in approvals]


@router.get("/{approval_id}", response_model=ApprovalResponse)
def get_approval(
    approval_id: UUID,
    current_user: CurrentUser,
) -> ApprovalResponse:
    try:
        approval = ApprovalsService.get_approval(approval_id, current_user.id)
    except ApprovalNotFoundError as exc:
        _raise_http_exception(exc)

    return to_approval_response(approval)


@router.patch("/{approval_id}", response_model=ApprovalResponse)
def update_approval(
    approval_id: UUID,
    payload: UpdateApprovalRequest,
    current_user: CurrentUser,
) -> ApprovalResponse:
    try:
        approval = ApprovalsService.update_approval(
            approval_id,
            current_user.id,
            title=payload.title,
            description=payload.description,
            status=payload.status,
        )
    except (ApprovalNotFoundError, InvalidApprovalValueError) as exc:
        _raise_http_exception(exc)

    return to_approval_response(approval)


@router.delete("/{approval_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_approval(approval_id: UUID, current_user: CurrentUser) -> None:
    try:
        ApprovalsService.delete_approval(approval_id, current_user.id)
    except ApprovalNotFoundError as exc:
        _raise_http_exception(exc)
