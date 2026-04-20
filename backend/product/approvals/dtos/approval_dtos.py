from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True, frozen=True)
class Approval:
    id: UUID
    title: str
    description: str
    status: str
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
