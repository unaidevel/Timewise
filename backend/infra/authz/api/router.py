from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from infra.authz.api.dependencies import (
    RateLimitedUser,
    bearer_security,
    get_client_context,
)
from infra.authz.dtos.dtos import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    UpdateEmailRequest,
    UpdateNameRequest,
    UpdatePasswordRequest,
    UserResponse,
)
from infra.authz.dtos.mappers.auth_mapper import to_login_response, to_user_response
from infra.authz.services.auth_service import AuthService
from infra.common.exceptions import (
    Conflict,
    NotFound,
    TooManyRequests,
    Unauthorized,
    UnprocessableEntity,
    responses_for,
)
from infra.common.rate_limiting import (
    AUTH_RATE_LIMIT,
    USER_RATE_LIMIT,
    limiter,
    user_or_ip_key,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    responses=responses_for(Conflict, UnprocessableEntity, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(AUTH_RATE_LIMIT)
def register(payload: RegisterRequest, request: Request) -> UserResponse:
    """
    Creates a new user account from email, full_name, and password.
    Returns the created user as UserResponse with HTTP 201.
    On error returns 409 (email taken), 422 (weak password / invalid fields), or 429 (rate limit).
    Rate-limited by the global AUTH_RATE_LIMIT; password is hashed before persisting.
    """
    user = AuthService.register_user(
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
    )
    return to_user_response(user)


@router.post(
    "/login",
    response_model=LoginResponse,
    responses=responses_for(Unauthorized, UnprocessableEntity, TooManyRequests),
)
@limiter.limit(AUTH_RATE_LIMIT)
def login_user(payload: LoginRequest, request: Request) -> LoginResponse:
    """
    Authenticates a user with email + password and issues a session.
    Returns LoginResponse with access_token, refresh_token, and user payload.
    On error returns 401 (invalid credentials), 422 (malformed body), or 429 (rate limit).
    Captures client IP and user-agent into the session for refresh-token binding.
    """
    session = AuthService.login(
        email=payload.email,
        password=payload.password,
        client=get_client_context(request),
    )
    return to_login_response(session)


@router.get(
    "/me",
    response_model=UserResponse,
    responses=responses_for(Unauthorized, TooManyRequests),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def get_me(request: Request, current_user: RateLimitedUser) -> UserResponse:
    """
    Returns the profile of the authenticated user identified by the bearer token.
    Responds with UserResponse containing id, email, and full_name.
    On error returns 401 (missing/invalid token) or 429 (rate limit).
    Rate-limited per-user (or per-IP for anonymous) via USER_RATE_LIMIT.
    """
    return to_user_response(current_user)


@router.post(
    "/refresh",
    response_model=LoginResponse,
    responses=responses_for(Unauthorized, TooManyRequests),
)
@limiter.limit(AUTH_RATE_LIMIT)
def refresh_token(payload: RefreshRequest, request: Request) -> LoginResponse:
    """
    Rotates a valid refresh token and issues a new access/refresh pair.
    Returns LoginResponse with the freshly issued tokens and user payload.
    On error returns 401 (revoked/expired/reused refresh token) or 429 (rate limit).
    Reuse detection revokes the entire token family for safety.
    """
    session = AuthService.refresh(payload.refresh_token, get_client_context(request))
    return to_login_response(session)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_security),
) -> None:
    """
    Revokes the refresh-token family tied to the supplied bearer token.
    Returns HTTP 204 with no body on success.
    Always succeeds: missing/invalid tokens are treated as no-ops so logout is idempotent.
    Does not invalidate already-issued access tokens (they expire naturally).
    """
    if credentials:
        AuthService.logout(credentials.credentials)


@router.put(
    "/me/name",
    response_model=UserResponse,
    responses=responses_for(
        Unauthorized, NotFound, UnprocessableEntity, TooManyRequests
    ),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def update_my_name(
    payload: UpdateNameRequest,
    current_user: RateLimitedUser,
    request: Request,
) -> UserResponse:
    """
    Updates the authenticated user's full_name to the value in the payload.
    Returns UserResponse reflecting the updated user.
    On error returns 401 (unauthenticated), 404 (user not found), 422 (invalid name), or 429 (rate limit).
    Rate-limited per-user; mutates only AuthUser.full_name and updated_at.
    """
    user = AuthService.update_user_name(current_user.id, payload.full_name)
    return to_user_response(user)


@router.put(
    "/me/email",
    response_model=UserResponse,
    responses=responses_for(
        Unauthorized,
        NotFound,
        Conflict,
        UnprocessableEntity,
        TooManyRequests,
    ),
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def update_my_email(
    payload: UpdateEmailRequest,
    current_user: RateLimitedUser,
    request: Request,
) -> UserResponse:
    """
    Updates the authenticated user's email immediately (no verification step).
    Returns UserResponse with the new email.
    On error returns 401, 404 (user missing), 409 (email already in use), 422 (invalid email), or 429.
    Email uniqueness is enforced at the database layer; conflict surfaces as 409.
    """
    user = AuthService.update_user_email(current_user.id, payload.email)
    return to_user_response(user)


@router.put(
    "/me/password",
    response_model=LoginResponse,
    responses=responses_for(
        Unauthorized, NotFound, UnprocessableEntity, TooManyRequests
    ),
)
@limiter.limit(AUTH_RATE_LIMIT)
def update_my_password(
    payload: UpdatePasswordRequest,
    current_user: RateLimitedUser,
    request: Request,
) -> LoginResponse:
    """
    Changes the user's password after verifying the current one, then rotates the session.
    Returns LoginResponse with a fresh access/refresh pair so the caller stays logged in.
    On error returns 401 (wrong current password / no token), 404, 422 (weak new password), or 429.
    Revokes ALL other refresh tokens for the user — other devices are logged out.
    """
    user = AuthService.update_user_password(
        current_user.id,
        payload.current_password,
        payload.new_password,
    )
    session = AuthService.rotate_session_after_password_change(
        user, client=get_client_context(request)
    )
    return to_login_response(session)
