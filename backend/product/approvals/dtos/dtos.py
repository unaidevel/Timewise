from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CreateApprovalRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)


class UpdateApprovalRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: str | None = Field(default=None, min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_has_updates(self) -> "UpdateApprovalRequest":
        if self.title is None and self.description is None and self.status is None:
            raise ValueError("At least one field must be provided.")

        return self


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: str
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
