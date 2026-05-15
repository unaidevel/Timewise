from typing import Annotated

from django.conf import settings
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from infra.authz.dtos.auth_dtos import AuthUser, ClientContext
from infra.authz.services.auth_service import AuthService

bearer_security = HTTPBearer(auto_error=False)


def unauthorized_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_security),
) -> AuthUser:
    access_token = credentials.credentials if credentials else ""
    user = AuthService.authenticate(access_token)
    if not user:
        raise unauthorized_exception("Invalid or expired token")

    return user


def _direct_client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _resolve_client_ip(request: Request) -> str:
    direct_ip = _direct_client_ip(request)

    trust_proxy: bool = getattr(settings, "AUTH_TRUST_PROXY_HEADERS", False)
    if not trust_proxy:
        return direct_ip

    trusted_proxies: list[str] = getattr(settings, "AUTH_TRUSTED_PROXIES", []) or []
    if trusted_proxies and direct_ip not in trusted_proxies:
        return direct_ip

    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        # Left-most non-trusted entry is the original client.
        candidates = [part.strip() for part in forwarded_for.split(",") if part.strip()]
        for candidate in candidates:
            if not trusted_proxies or candidate not in trusted_proxies:
                return candidate
        if candidates:
            return candidates[0]

    real_ip = request.headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip

    return direct_ip


def get_client_context(request: Request) -> ClientContext:
    return ClientContext(
        ip=_resolve_client_ip(request),
        user_agent=request.headers.get("user-agent", ""),
    )


def get_current_user_stamped(
    request: Request,
    user: AuthUser = Depends(get_current_user),
) -> AuthUser:
    """get_current_user + stamps user id on request.state for per-user rate limits."""
    request.state.rate_limit_user_id = user.id
    return user


CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
RateLimitedUser = Annotated[AuthUser, Depends(get_current_user_stamped)]
CurrentClient = Annotated[ClientContext, Depends(get_client_context)]
