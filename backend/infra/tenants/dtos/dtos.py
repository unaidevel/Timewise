from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateTenantRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=100)


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    is_active: bool
    created_at: datetime


class AddMemberRequest(BaseModel):
    user_id: UUID
    role: str = Field(pattern=r"^(owner|admin|member)$")


class TenantMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime
    invited_by_id: UUID | None
    left_at: datetime | None
    left_reason: str | None
