"""HTTP rate limiting for the FastAPI surface.

Storage is in-process (``memory://``) — correct for a single uvicorn worker.
For multi-worker / multi-container deployments, swap ``RATE_LIMIT_STORAGE_URI``
to a shared backend (e.g. ``redis://...``).

Usage
-----

Per-IP limits on unauthenticated routes (e.g. /login, /register, /refresh)::

    from infra.common.rate_limiting import AUTH_RATE_LIMIT, limiter

    @router.post("/login")
    @limiter.limit(AUTH_RATE_LIMIT)
    def login_user(payload: LoginRequest, request: Request) -> ...

Per-user limits on authenticated routes — opt-in by decorating with
``limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)``. ``get_current_user``
stamps ``request.state.rate_limit_user_id`` so the key resolves to the user
once authenticated.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from slowapi import Limiter

from infra.authz.api.dependencies import _resolve_client_ip
from infra.common.exceptions import TooManyRequests

if TYPE_CHECKING:
    from fastapi import Request
    from slowapi.errors import RateLimitExceeded


def client_ip_key(request: Request) -> str:
    return _resolve_client_ip(request)


def user_or_ip_key(request: Request) -> str:
    user_id = getattr(request.state, "rate_limit_user_id", None)
    if user_id:
        return f"user:{user_id}"
    return f"ip:{_resolve_client_ip(request)}"


limiter = Limiter(
    key_func=client_ip_key,
    storage_uri=getattr(settings, "RATE_LIMIT_STORAGE_URI", "memory://"),
    default_limits=[],
    headers_enabled=False,
    enabled=getattr(settings, "RATE_LIMIT_ENABLED", True),
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> None:
    raise TooManyRequests(f"Rate limit exceeded: {exc.detail}")


AUTH_RATE_LIMIT = getattr(settings, "RATE_LIMIT_AUTH", "5/minute")
USER_RATE_LIMIT = getattr(settings, "RATE_LIMIT_AUTHENTICATED", "1000/hour")
