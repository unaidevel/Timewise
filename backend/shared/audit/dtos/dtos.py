from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventIn(BaseModel):
    action: str = Field(min_length=1, max_length=100)
    resource_type: str = Field(min_length=1, max_length=100)
    resource_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


class AuditEventUpdate(BaseModel):
    notes: str = ""


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    actor_id: int
    action: str
    resource_type: str
    resource_id: int | None
    metadata: dict[str, Any]
    notes: str
    occurred_at: datetime
