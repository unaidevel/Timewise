from fastapi import APIRouter, Query, Request, status

from infra.authz.api.dependencies import RateLimitedUser
from infra.common.exceptions import (
    Forbidden,
    NotFound,
    TooManyRequests,
    UnprocessableEntity,
    responses_for,
)
from infra.common.rate_limiting import USER_RATE_LIMIT, limiter, user_or_ip_key
from shared.audit.dtos.dtos import AuditEventIn, AuditEventOut, AuditEventUpdate
from shared.audit.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/tenants/{tenant_id}", tags=["audit"])


@router.post(
    "/audit-events",
    response_model=AuditEventOut,
    responses=responses_for(Forbidden, UnprocessableEntity, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def record_event(
    tenant_id: int,
    payload: AuditEventIn,
    current_user: RateLimitedUser,
    request: Request,
) -> AuditEventOut:
    return AuditService.create(tenant_id, payload, current_user.id)


@router.get(
    "/audit-events",
    response_model=list[AuditEventOut],
    responses=responses_for(TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def list_events(
    tenant_id: int,
    current_user: RateLimitedUser,
    request: Request,
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    resource_id: int | None = Query(default=None),
    actor_id: int | None = Query(default=None),
    outcome: str | None = Query(default=None),
) -> list[AuditEventOut]:
    return AuditService.get_all(
        tenant_id,
        current_user.id,
        action,
        resource_type,
        resource_id,
        actor_id,
        outcome,
    )


@router.get(
    "/audit-events/{event_id}",
    response_model=AuditEventOut,
    responses=responses_for(NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def get_event(
    tenant_id: int,
    event_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> AuditEventOut:
    return AuditService.get_by_id(tenant_id, event_id, current_user.id)


@router.put(
    "/audit-events/{event_id}",
    response_model=AuditEventOut,
    responses=responses_for(Forbidden, NotFound, UnprocessableEntity, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def update_event(
    tenant_id: int,
    event_id: int,
    payload: AuditEventUpdate,
    current_user: RateLimitedUser,
    request: Request,
) -> AuditEventOut:
    return AuditService.update(tenant_id, event_id, payload, current_user.id)


@router.delete(
    "/audit-events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=responses_for(Forbidden, NotFound, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def delete_event(
    tenant_id: int,
    event_id: int,
    current_user: RateLimitedUser,
    request: Request,
) -> None:
    AuditService.delete(tenant_id, event_id, current_user.id)
