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


class TenantUpdate(TenantIn):
    tenant_id: int
    is_active: bool


class AddMemberRequest(BaseModel):
    user_id: int
    role: str = Field(pattern=r"^(owner|admin|manager|employee|freelance)$")


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


class OrganizationProfileIn(BaseModel):
    public_name: str = Field(default="", max_length=200)
    legal_name: str = Field(default="", max_length=200)
    country: str = Field(default="", max_length=2)
    timezone: str = Field(default="UTC", max_length=64)
    currency: str = Field(default="EUR", max_length=3)
    vat_number: str = Field(default="", max_length=32)


class OrganizationProfileOut(OrganizationProfileIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime


class TimezoneOption(BaseModel):
    value: str
    label: str
