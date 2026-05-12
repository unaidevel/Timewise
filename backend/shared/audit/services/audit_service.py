from infra.common.exceptions import NotFound
from infra.tenants.decorators import any_employee, only_admin
from shared.audit.dtos.dtos import AuditEventIn, AuditEventOut, AuditEventUpdate
from shared.audit.entities.audit_entities import (
    AuditEventEntity,
    AuditEventUpdateEntity,
)
from shared.audit.repositories.audit_repository import AuditRepository


class AuditService:
    @any_employee
    @staticmethod
    def create(
        tenant_id: int,
        payload: AuditEventIn,
        user_id: int,
    ) -> AuditEventOut:
        entity = AuditEventEntity(**payload.model_dump())
        return AuditRepository.create(entity, tenant_id, user_id)

    @any_employee
    @staticmethod
    def get_by_id(tenant_id: int, event_id: int, user_id: int) -> AuditEventOut:
        event = AuditRepository.get_by_id(event_id)
        if not event or event.tenant_id != tenant_id:
            raise NotFound(f"Audit event {event_id} not found.")
        return event

    @any_employee
    @staticmethod
    def get_all(
        tenant_id: int,
        user_id: int,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        actor_id: int | None = None,
        outcome: str | None = None,
    ) -> list[AuditEventOut]:
        return AuditRepository.get_all(
            tenant_id,
            action,
            resource_type,
            resource_id,
            actor_id,
            outcome,
        )

    @only_admin
    @staticmethod
    def update(
        tenant_id: int,
        event_id: int,
        payload: AuditEventUpdate,
        user_id: int,
    ) -> AuditEventOut:
        AuditService.get_by_id(tenant_id, event_id, user_id)
        entity = AuditEventUpdateEntity(event_id=event_id, **payload.model_dump())
        return AuditRepository.update(entity)

    @only_admin
    @staticmethod
    def delete(tenant_id: int, event_id: int, user_id: int) -> None:
        AuditService.get_by_id(tenant_id, event_id, user_id)
        AuditRepository.delete(event_id)
