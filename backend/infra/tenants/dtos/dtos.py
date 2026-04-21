from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TenantIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=100)


class TenantOut(TenantIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_id: int | None


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

    @field_validator("left_reason", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: object) -> object:
        return None if v == "" else v
