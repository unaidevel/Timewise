from fastapi import APIRouter, Request, status

from infra.authz.api.dependencies import RateLimitedUser
from infra.common.exceptions import (
    Conflict,
    NotFound,
    TooManyRequests,
    UnprocessableEntity,
    responses_for,
)
from infra.common.rate_limiting import USER_RATE_LIMIT, limiter, user_or_ip_key
from infra.tenants.dtos.dtos import (
    AddMemberRequest,
    TenantIn,
    TenantMemberResponse,
    TenantOut,
    TenantUpdate,
)
from infra.tenants.orchestrators.tenant_orchestrator import TenantOrchestrator
from infra.tenants.services.tenants_service import TenantService

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


@router.post(
    "",
    response_model=TenantOut,
    responses=responses_for(Conflict, UnprocessableEntity, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def create(
    payload: TenantIn, current_user: RateLimitedUser, request: Request
) -> TenantOut:
    return TenantOrchestrator.create(payload, current_user.id)


@router.get(
    "",
    response_model=list[TenantOut],
    responses=responses_for(TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_for_user(current_user: RateLimitedUser, request: Request) -> list[TenantOut]:
    return TenantService.list_for_user(current_user.id)


@router.put(
    "",
    response_model=TenantOut,
    responses=responses_for(NotFound, Conflict, UnprocessableEntity, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def update(
    payload: TenantUpdate, current_user: RateLimitedUser, request: Request
) -> TenantOut:
    return TenantService.update_tenant(payload, current_user.id)


@router.get(
    "/{tenant_id}",
    response_model=TenantOut,
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def get_by_id(
    tenant_id: int, current_user: RateLimitedUser, request: Request
) -> TenantOut:
    return TenantService.get_by_id(tenant_id, current_user.id)


@router.post(
    "/{tenant_id}/members",
    response_model=TenantMemberResponse,
    responses=responses_for(NotFound, Conflict, UnprocessableEntity, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def add_member(
    tenant_id: int,
    payload: AddMemberRequest,
    current_user: RateLimitedUser,
    request: Request,
) -> TenantMemberResponse:
    return TenantService.add_member(
        tenant_id,
        payload,
        current_user.id,
    )


@router.get(
    "/{tenant_id}/members",
    response_model=list[TenantMemberResponse],
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_members(
    tenant_id: int, _: RateLimitedUser, request: Request
) -> list[TenantMemberResponse]:
    return TenantService.list_members(tenant_id)


@router.delete(
    "/{tenant_id}/members/{membership_id}",
    response_model=TenantMemberResponse,
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def remove_member(
    tenant_id: int,
    membership_id: int,
    _: RateLimitedUser,
    request: Request,
    reason: str = "",
) -> TenantMemberResponse:
    return TenantService.remove_member(
        tenant_id,
        membership_id,
        reason,
    )
