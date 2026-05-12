import contextlib
from typing import Any

from django.db import models, transaction

from infra.common.exceptions import (
    Conflict,
    Forbidden,
    NotFound,
    UnprocessableEntity,
)


class AuditOutcome(models.TextChoices):
    SUCCESS = "success", "Success"
    FAILURE = "failure", "Failure"


AUDITED_FAILURES: tuple[type[Exception], ...] = (
    Conflict,
    NotFound,
    UnprocessableEntity,
    Forbidden,
)


def record_failure(
    tenant_id: int,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: int | None,
    metadata: dict[str, Any],
    exc: Exception,
) -> None:
    """Persist a failure audit event in its own transaction.

    Swallows all exceptions: losing the failure audit must not compound
    a business error. `AuditService` and `AuditEventIn` are imported
    lazily here because `models.py` imports `AuditOutcome` from this
    module, and both of those transitively import `models.py` — eager
    imports would be circular.
    """
    from shared.audit.dtos.dtos import AuditEventIn
    from shared.audit.services.audit_service import AuditService

    failure_metadata = {
        **metadata,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
    }
    with contextlib.suppress(Exception), transaction.atomic():
        AuditService.create(
            tenant_id,
            AuditEventIn(
                action=action,
                resource_type=resource_type,
                outcome=AuditOutcome.FAILURE.value,
                resource_id=resource_id,
                metadata=failure_metadata,
            ),
            user_id,
        )
