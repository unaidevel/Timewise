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
    return to_user_response(current_user)


@router.post(
    "/refresh",
    response_model=LoginResponse,
    responses=responses_for(Unauthorized, TooManyRequests),
)
@limiter.limit(AUTH_RATE_LIMIT)
def refresh_token(payload: RefreshRequest, request: Request) -> LoginResponse:
    session = AuthService.refresh(payload.refresh_token, get_client_context(request))
    return to_login_response(session)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_security),
) -> None:
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
    user = AuthService.update_user_password(
        current_user.id,
        payload.current_password,
        payload.new_password,
    )
    session = AuthService.rotate_session_after_password_change(
        user, client=get_client_context(request)
    )
    return to_login_response(session)
