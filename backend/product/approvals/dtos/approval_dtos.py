from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class Approval:
    id: int
    title: str
    description: str
    status: str
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
