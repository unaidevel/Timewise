from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TenantIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=100)


class TenantOut(TenantIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AddMemberRequest(BaseModel):
    user_id: int
    role: str = Field(pattern=r"^(owner|creator|admin|member)$")


class TenantMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    user_id: int
    role: str
    joined_at: datetime
    invited_by_id: int | None
    left_at: datetime | None
    left_reason: str | None
