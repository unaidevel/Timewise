from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from infra.authz.dtos.auth_dtos import AuthUser
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


CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
