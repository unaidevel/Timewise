import contextlib
from typing import Any

from django.db import transaction

from infra.common.exceptions import (
    Conflict,
    Forbidden,
    NotFound,
    UnprocessableEntity,
)
from shared.audit.dtos.dtos import AuditEventIn
from shared.audit.models import AuditOutcome
from shared.audit.services.audit_service import AuditService

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
    a business error.
    """
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
                resource_id=resource_id,
                outcome=AuditOutcome.FAILURE.value,
                metadata=failure_metadata,
            ),
            user_id,
        )
