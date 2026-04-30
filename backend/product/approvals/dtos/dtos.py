from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RejectApprovalIn(BaseModel):
    reason: str = Field(default="", max_length=2000)


class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    report_id: int
    status: str
    reviewer_id: int | None
    reviewed_at: datetime | None
    created_by_id: int | None
    created_at: datetime
    updated_at: datetime


class ApprovalEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    approval_id: int
    action: str
    actor_id: int
    reason: str
    actioned_at: datetime
