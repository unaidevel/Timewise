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
    """
    Creates a new tenant and makes the caller its first owner-member.
    Returns TenantOut with HTTP 201 carrying tenant id, name, slug, and timestamps.
    On error returns 409 (slug already taken), 422 (invalid fields), or 429 (rate limit).
    Wraps tenant + initial membership creation in a single orchestrator step.
    """
    return TenantOrchestrator.create(payload, current_user.id)


@router.get(
    "",
    response_model=list[TenantOut],
    responses=responses_for(TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_for_user(current_user: RateLimitedUser, request: Request) -> list[TenantOut]:
    """
    Lists every tenant the authenticated user is currently a member of.
    Returns a list[TenantOut]; the array is empty if the user has no memberships.
    On error returns 429 (rate limit); authentication is enforced by the dependency.
    Result is scoped to active memberships only — revoked ones are excluded.
    """
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
    """
    Updates the tenant identified inside the payload (name/slug/etc.).
    Returns TenantOut with the post-update tenant snapshot.
    On error returns 404 (tenant missing), 409 (slug collision), 422 (invalid fields), or 429.
    Requires the caller to be an owner of the target tenant.
    """
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
    """
    Fetches a single tenant by id, after verifying the caller is a member.
    Returns TenantOut with the tenant detail.
    On error returns 404 (tenant missing or caller not a member) or 429 (rate limit).
    Non-membership is intentionally returned as 404 to avoid leaking tenant existence.
    """
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
    """
    Adds a user to the tenant with the role supplied in the payload.
    Returns TenantMemberResponse with HTTP 201 describing the new membership.
    On error returns 404 (tenant or user missing), 409 (already a member), 422, or 429.
    Caller must be an owner; cannot be used to invite by email — user must already exist.
    """
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
    """
    Lists every active membership row for the given tenant.
    Returns list[TenantMemberResponse] with per-member role and user details.
    On error returns 404 (tenant not found) or 429 (rate limit).
    Soft-removed memberships are filtered out — only currently active members appear.
    """
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
    """
    Soft-removes a membership from the tenant, storing the optional 'reason' query string.
    Returns TenantMemberResponse showing the now-revoked membership.
    On error returns 404 (membership not found in this tenant) or 429 (rate limit).
    Soft delete: row is preserved with a revoked_at stamp so the audit history stays intact.
    """
    return TenantService.remove_member(
        tenant_id,
        membership_id,
        reason,
    )
