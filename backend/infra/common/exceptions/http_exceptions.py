from typing import Any

from fastapi import HTTPException


class AppHTTPException(HTTPException):
    """Base for all typed HTTP exceptions in this project.

    Subclasses declare ``status_code`` and ``description`` as class attributes.
    Raising ``SomeDomainError("message")`` propagates *message* as the HTTP
    ``detail`` field; FastAPI handles the response automatically.
    """

    status_code: int = 500
    description: str = "Internal Server Error"

    def __init__(self, detail: Any = None) -> None:
        super().__init__(
            status_code=type(self).status_code,
            detail=detail if detail is not None else type(self).description,
        )


class BadRequest(AppHTTPException):
    status_code = 400
    description = "Bad Request"


class Unauthorized(AppHTTPException):
    status_code = 401
    description = "Unauthorized"

    def __init__(self, detail: Any = None) -> None:
        super().__init__(detail)
        self.headers = {"WWW-Authenticate": "Bearer"}


class Forbidden(AppHTTPException):
    status_code = 403
    description = "Forbidden"


class NotFound(AppHTTPException):
    status_code = 404
    description = "Not Found"


class Conflict(AppHTTPException):
    status_code = 409
    description = "Conflict"


class UnprocessableEntity(AppHTTPException):
    status_code = 422
    description = "Unprocessable Entity"


class TooManyRequests(AppHTTPException):
    status_code = 429
    description = "Too Many Requests"


class InternalServerError(AppHTTPException):
    status_code = 500
    description = "Internal Server Error"


class ServiceUnavailable(AppHTTPException):
    status_code = 503
    description = "Service Unavailable"
