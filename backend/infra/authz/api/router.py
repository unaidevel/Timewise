from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from infra.authz.dtos.auth_dtos import AuthUser
from infra.authz.dtos.dtos import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
)
from infra.authz.dtos.mappers.auth_mapper import to_login_response, to_user_response
from infra.authz.services.auth_service import AuthService
from infra.common.exceptions import (
    EmailAlreadyExistsError,
    InvalidAuthValueError,
    InvalidCredentialsError,
    TooManyLoginAttemptsError,
    WeakPasswordError,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


def _unauthorized_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _get_client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthUser:
    access_token = credentials.credentials if credentials else ""
    user = AuthService.authenticate(access_token)
    if not user:
        raise _unauthorized_exception("Invalid or expired token")
    return user


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(payload: RegisterRequest) -> UserResponse:
    try:
        user = AuthService.register_user(
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password,
        )
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except InvalidAuthValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except WeakPasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.messages,
        ) from exc

    return to_user_response(user)


@router.post("/login", response_model=LoginResponse)
def login_user(payload: LoginRequest, request: Request) -> LoginResponse:
    try:
        session = AuthService.login(
            email=payload.email,
            password=payload.password,
            client_ip=_get_client_ip(request),
        )
    except InvalidAuthValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except InvalidCredentialsError as exc:
        raise _unauthorized_exception(str(exc)) from exc
    except TooManyLoginAttemptsError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)
        ) from exc

    return to_login_response(session)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: AuthUser = Depends(get_current_user)) -> UserResponse:
    return to_user_response(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> None:
    if credentials:
        AuthService.logout(credentials.credentials)
