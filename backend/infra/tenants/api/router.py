from fastapi import APIRouter, HTTPException, status

from infra.authz.api.dependencies import CurrentUser
from infra.common.responses import STATUS_RESPONSES
from infra.tenants.dtos.dtos import (
    AddMemberRequest,
    TenantIn,
    TenantMemberResponse,
    TenantOut,
)
from infra.tenants.dtos.mappers.tenant_mapper import (
    to_tenant_member_response,
    to_tenant_response,
)
from infra.tenants.exceptions import (
    MemberAlreadyExistsError,
    MemberNotFoundError,
    TenantAlreadyExistsError,
    TenantNotFoundError,
)
from infra.tenants.services.tenants_service import TenantService

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


@router.post("", response_model=TenantOut, responses=STATUS_RESPONSES, status_code=status.HTTP_201_CREATED)
def create_tenant(payload: TenantIn, current_user: CurrentUser) -> TenantOut:
    try:
        tenant = TenantService.create(payload=payload, created_by_id=current_user.id)
    except TenantAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return to_tenant_response(tenant)


@router.get("", response_model=list[TenantOut])
def list_tenants(_: CurrentUser) -> list[TenantOut]:
    return [to_tenant_response(tenant) for tenant in TenantService.list_all()]


@router.get("/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: int, _: CurrentUser) -> TenantOut:
    try:
        tenant = TenantService.get_by_id(tenant_id)
    except TenantNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return to_tenant_response(tenant)


@router.post(
    "/{tenant_id}/members",
    response_model=TenantMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    tenant_id: int,
    payload: AddMemberRequest,
    current_user: CurrentUser,
) -> TenantMemberResponse:
    try:
        membership = TenantService.add_member(
            tenant_id=tenant_id,
            user_id=payload.user_id,
            role=payload.role,
            invited_by_id=current_user.id,
        )
    except TenantNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MemberAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return to_tenant_member_response(membership)


@router.get("/{tenant_id}/members", response_model=list[TenantMemberResponse])
def list_members(tenant_id: int, _: CurrentUser) -> list[TenantMemberResponse]:
    try:
        memberships = TenantService.list_members(tenant_id)
    except TenantNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [to_tenant_member_response(m) for m in memberships]


@router.delete(
    "/{tenant_id}/members/{membership_id}",
    response_model=TenantMemberResponse,
)
def remove_member(
    tenant_id: int,
    membership_id: int,
    reason: str = "",
    _: CurrentUser = None,
) -> TenantMemberResponse:
    try:
        membership = TenantService.remove_member(
            tenant_id=tenant_id,
            membership_id=membership_id,
            reason=reason,
        )
    except TenantNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MemberNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return to_tenant_member_response(membership)
