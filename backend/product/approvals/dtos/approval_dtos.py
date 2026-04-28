from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class ReportApproval:
    id: int
    tenant_id: int
    report_id: int
    status: str
    reviewer_id: int | None
    reviewed_at: datetime | None
    created_by_id: int | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True, frozen=True)
class ReportApprovalEvent:
    id: int
    approval_id: int
    action: str
    actor_id: int
    reason: str
    actioned_at: datetime
