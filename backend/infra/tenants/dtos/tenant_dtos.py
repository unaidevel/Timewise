from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Tenant:
    id: UUID
    name: str
    slug: str
    is_active: bool
    created_at: datetime
    created_by_id: UUID | None


@dataclass(frozen=True, slots=True)
class TenantMembership:
    id: UUID
    tenant_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime
    invited_by_id: UUID | None
    left_at: datetime | None
    left_reason: str | None
