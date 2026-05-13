from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuthUser(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: int
    email: str
    full_name: str
    password_hash: str
    is_active: bool
    created_at: datetime


class AuthToken(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: int
    user: AuthUser
    family_id: str
    token_hash: str
    expires_at: datetime
    refresh_token_hash: str
    refresh_expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime
    client_ip: str
    user_agent: str


class AuthSession(BaseModel):
    model_config = ConfigDict(frozen=True)

    access_token: str
    refresh_token: str
    token_type: str
    expires_at: datetime
    refresh_expires_at: datetime
    user: AuthUser


class ClientContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    ip: str
    user_agent: str
