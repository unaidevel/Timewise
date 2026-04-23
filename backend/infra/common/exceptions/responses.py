from infra.common.exceptions.http_exceptions import AppHTTPException

STATUS_RESPONSES = {
    401: {"description": "Unauthorized"},
    403: {"description": "Forbidden"},
    404: {"description": "Not Found"},
    409: {"description": "Conflict"},
    422: {"description": "Unprocessable Entity"},
}


def responses_for(*exc_types: type[AppHTTPException]) -> dict[int, dict]:
    """
    Build FastAPI responses dict from typed HTTP exception classes.

    Always include it in responses parameter:
        @router.get("/foo", responses=responses_for(NotFound, Forbidden))
        def get_by_id():
    """
    return {
        exc_type.status_code: {"description": exc_type.description}
        for exc_type in exc_types
    }
