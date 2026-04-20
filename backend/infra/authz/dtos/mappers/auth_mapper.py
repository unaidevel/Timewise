from infra.authz.dtos.auth_dtos import AuthSession, AuthUser
from infra.authz.dtos.dtos import LoginResponse, UserResponse


def to_user_response(user: AuthUser) -> UserResponse:
    return UserResponse.model_validate(user)


def to_login_response(session: AuthSession) -> LoginResponse:
    return LoginResponse(
        access_token=session.access_token,
        token_type=session.token_type,
        expires_at=session.expires_at,
        user=to_user_response(session.user),
    )
