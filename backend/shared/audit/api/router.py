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
    """
    Records a single audit event under the tenant, stamping actor + tenant from the caller's context.
    Returns AuditEventOut with HTTP 201 carrying the persisted event row.
    On error returns 403 (caller lacks audit write rights), 422 (invalid action/resource), or 429.
    Designed for app-internal callers; values are stored verbatim and are not freely editable later.
    """
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
    """
    Lists audit events for the tenant with optional filters (action, resource, actor, outcome).
    Returns list[AuditEventOut]; the array is empty when no events match the filters.
    On error returns 429 (rate limit); the tenant scope is always enforced regardless of filters.
    All filters are AND-ed together; supplying none returns every event for the tenant.
    """
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
    """
    Fetches a single audit event by id, scoped to the tenant.
    Returns AuditEventOut with the full event payload (actor, action, resource, outcome, metadata).
    On error returns 404 (event missing or belongs to a different tenant) or 429 (rate limit).
    Cross-tenant lookups are blocked even if the event id is known.
    """
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
    """
    Patches a mutable subset of fields on an existing audit event (e.g., outcome or metadata).
    Returns AuditEventOut with the post-update event row.
    On error returns 403 (caller lacks write rights), 404 (event missing), 422, or 429.
    Core fields (actor, tenant, action, timestamp) remain immutable to preserve auditability.
    """
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
    """
    Deletes an audit event scoped to the tenant; intended for compliance-driven scrubbing only.
    Returns HTTP 204 with no body on success.
    On error returns 403 (caller lacks delete rights), 404 (event missing), or 429 (rate limit).
    Hard delete — the row is removed; restrict to admin/compliance flows in callers.
    """
    AuditService.delete(tenant_id, event_id, current_user.id)
