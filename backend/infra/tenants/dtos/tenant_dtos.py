from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Tenant:
    id: int
    name: str
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_id: int | None


@dataclass(frozen=True, slots=True)
class TenantMembership:
    id: int
    tenant_id: int
    user_id: int
    role: str
    joined_at: datetime
    invited_by_id: int | None
    left_at: datetime | None
    left_reason: str | None
