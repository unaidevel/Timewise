from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from infra.authz.api.dependencies import (
    CurrentUser,
    bearer_security,
    get_current_user,
)
from infra.authz.dtos.dtos import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    UserResponse,
)
from infra.authz.dtos.mappers.auth_mapper import to_login_response, to_user_response
from infra.authz.services.auth_service import AuthService
from infra.common.exceptions import (
    Conflict,
    TooManyRequests,
    Unauthorized,
    UnprocessableEntity,
    responses_for,
)


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
__all__ = ["router", "get_current_user"]


def _get_client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


@router.post(
    "/register",
    response_model=UserResponse,
    responses=responses_for(Conflict, UnprocessableEntity),
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest) -> UserResponse:
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
def login_user(payload: LoginRequest, request: Request) -> LoginResponse:
    session = AuthService.login(
        email=payload.email,
        password=payload.password,
        client_ip=_get_client_ip(request),
    )
    return to_login_response(session)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUser) -> UserResponse:
    return to_user_response(current_user)


@router.post(
    "/refresh",
    response_model=LoginResponse,
    responses=responses_for(Unauthorized),
)
def refresh_token(payload: RefreshRequest) -> LoginResponse:
    session = AuthService.refresh(payload.refresh_token)
    return to_login_response(session)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_security),
) -> None:
    if credentials:
        AuthService.logout(credentials.credentials)
