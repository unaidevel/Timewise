from fastapi import APIRouter, Query, status

from infra.authz.api.dependencies import CurrentUser
from infra.common.exceptions import (
    Forbidden,
    NotFound,
    UnprocessableEntity,
    responses_for,
)
from shared.audit.dtos.dtos import AuditEventIn, AuditEventOut, AuditEventUpdate
from shared.audit.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/tenants/{tenant_id}", tags=["audit"])


@router.post(
    "/audit-events",
    response_model=AuditEventOut,
    responses=responses_for(Forbidden, UnprocessableEntity),
    status_code=status.HTTP_201_CREATED,
)
def record_event(
    tenant_id: int,
    payload: AuditEventIn,
    current_user: CurrentUser,
) -> AuditEventOut:
    return AuditService.create(tenant_id, payload, current_user.id)


@router.get("/audit-events", response_model=list[AuditEventOut])
def list_events(
    tenant_id: int,
    current_user: CurrentUser,
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
    responses=responses_for(NotFound),
)
def get_event(
    tenant_id: int, event_id: int, current_user: CurrentUser
) -> AuditEventOut:
    return AuditService.get_by_id(tenant_id, event_id, current_user.id)


@router.put(
    "/audit-events/{event_id}",
    response_model=AuditEventOut,
    responses=responses_for(Forbidden, NotFound, UnprocessableEntity),
)
def update_event(
    tenant_id: int,
    event_id: int,
    payload: AuditEventUpdate,
    current_user: CurrentUser,
) -> AuditEventOut:
    return AuditService.update(tenant_id, event_id, payload, current_user.id)


@router.delete(
    "/audit-events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=responses_for(Forbidden, NotFound),
)
def delete_event(tenant_id: int, event_id: int, current_user: CurrentUser) -> None:
    AuditService.delete(tenant_id, event_id, current_user.id)
