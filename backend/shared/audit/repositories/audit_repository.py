from shared.audit.dtos.dtos import AuditEventOut
from shared.audit.entities.audit_entities import (
    AuditEventEntity,
    AuditEventUpdateEntity,
)
from shared.audit.models import AuditEventModel


class AuditRepository:
    @staticmethod
    def create(
        entity: AuditEventEntity,
        tenant_id: int,
        user_id: int,
    ) -> AuditEventOut:
        if not isinstance(entity, AuditEventEntity):
            raise TypeError(f"Expected AuditEventEntity, got {type(entity).__name__}")
        return AuditEventOut.model_validate(
            AuditEventModel.objects.create(
                tenant_id=tenant_id,
                actor_id=user_id,
                action=entity.action,
                outcome=entity.outcome,
                resource_type=entity.resource_type,
                resource_id=entity.resource_id,
                metadata=entity.metadata,
                notes=entity.notes,
            )
        )

    @staticmethod
    def get_by_id(event_id: int) -> AuditEventOut | None:
        model = AuditEventModel.objects.filter(id=event_id).first()
        return AuditEventOut.model_validate(model) if model else None

    @staticmethod
    def get_all(
        tenant_id: int,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        actor_id: int | None = None,
        outcome: str | None = None,
    ) -> list[AuditEventOut]:
        qs = AuditEventModel.objects.filter(tenant_id=tenant_id)
        if action is not None:
            qs = qs.filter(action=action)
        if resource_type is not None:
            qs = qs.filter(resource_type=resource_type)
        if resource_id is not None:
            qs = qs.filter(resource_id=resource_id)
        if actor_id is not None:
            qs = qs.filter(actor_id=actor_id)
        if outcome is not None:
            qs = qs.filter(outcome=outcome)
        return [AuditEventOut.model_validate(m) for m in qs.order_by("-occurred_at")]

    @staticmethod
    def update(entity: AuditEventUpdateEntity) -> AuditEventOut | None:
        if not isinstance(entity, AuditEventUpdateEntity):
            raise TypeError(
                f"Expected AuditEventUpdateEntity, got {type(entity).__name__}"
            )
        rows = AuditEventModel.objects.filter(id=entity.event_id).update(
            notes=entity.notes
        )
        if rows == 0:
            return None
        return AuditEventOut.model_validate(
            AuditEventModel.objects.get(id=entity.event_id)
        )

    @staticmethod
    def delete(event_id: int) -> int:
        rows, _ = AuditEventModel.objects.filter(id=event_id).delete()
        return rows
