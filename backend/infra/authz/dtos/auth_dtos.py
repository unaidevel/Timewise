from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class AuthUser:
    id: int
    email: str
    full_name: str
    password_hash: str
    is_active: bool
    created_at: datetime


@dataclass(slots=True, frozen=True)
class AuthToken:
    id: int
    user: AuthUser
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime


@dataclass(slots=True, frozen=True)
class AuthSession:
    access_token: str
    token_type: str
    expires_at: datetime
    user: AuthUser
