from fastapi import APIRouter, status

from infra.authz.api.dependencies import CurrentUser
from infra.common.exceptions import (
    Conflict,
    NotFound,
    UnprocessableEntity,
    responses_for,
)
from infra.tenants.dtos.dtos import (
    AddMemberRequest,
    TenantIn,
    TenantMemberResponse,
    TenantOut,
)
from infra.tenants.orchestrators.tenant_orchestrator import TenantOrchestrator
from infra.tenants.services.tenants_service import TenantService

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


@router.post(
    "",
    response_model=TenantOut,
    responses=responses_for(Conflict, UnprocessableEntity),
    status_code=status.HTTP_201_CREATED,
)
def create_tenant(payload: TenantIn, current_user: CurrentUser) -> TenantOut:
    return TenantOrchestrator.create(payload=payload, created_by_id=current_user.id)


@router.get("", response_model=list[TenantOut])
def list_tenants(_: CurrentUser) -> list[TenantOut]:
    return TenantService.list_all()


@router.get("/{tenant_id}", response_model=TenantOut, responses=responses_for(NotFound))
def get_tenant(tenant_id: int, _: CurrentUser) -> TenantOut:
    return TenantService.get_by_id(tenant_id)


@router.post(
    "/{tenant_id}/members",
    response_model=TenantMemberResponse,
    responses=responses_for(NotFound, Conflict, UnprocessableEntity),
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    tenant_id: int,
    payload: AddMemberRequest,
    current_user: CurrentUser,
) -> TenantMemberResponse:
    return TenantService.add_member(
        tenant_id=tenant_id,
        payload=payload,
        invited_by_id=current_user.id,
    )


@router.get(
    "/{tenant_id}/members",
    response_model=list[TenantMemberResponse],
    responses=responses_for(NotFound),
)
def list_members(tenant_id: int, _: CurrentUser) -> list[TenantMemberResponse]:
    return TenantService.list_members(tenant_id)


@router.delete(
    "/{tenant_id}/members/{membership_id}",
    response_model=TenantMemberResponse,
    responses=responses_for(NotFound),
)
def remove_member(
    tenant_id: int,
    membership_id: int,
    reason: str = "",
    _: CurrentUser = None,
) -> TenantMemberResponse:
    return TenantService.remove_member(
        tenant_id=tenant_id,
        membership_id=membership_id,
        reason=reason,
    )
