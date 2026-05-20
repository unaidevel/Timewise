from fastapi import APIRouter, Request, status

from infra.authz.api.dependencies import RateLimitedUser
from infra.common.exceptions import (
    Conflict,
    Forbidden,
    NotFound,
    TooManyRequests,
    responses_for,
)
from infra.common.rate_limiting import USER_RATE_LIMIT, limiter, user_or_ip_key
from product.demo_data.orchestrators.demo_data_orchestrator import (
    DemoDataOrchestrator,
)

router = APIRouter(prefix="/api/v1/tenants", tags=["demo-data"])


@router.post(
    "/{tenant_id}/demo-data",
    response_model=dict[str, int],
    responses=responses_for(Conflict, Forbidden, NotFound, TooManyRequests),
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(USER_RATE_LIMIT, key_func=user_or_ip_key)
def seed_demo_data(
    tenant_id: int, current_user: RateLimitedUser, request: Request
) -> dict[str, int]:
    """
    Seeds the given tenant with a deterministic set of demo employees, periods, reports, and rules.
    Returns dict[str, int] with HTTP 201 mapping each seeded resource type to a count.
    On error returns 403 (caller not owner), 404 (tenant missing), 409 (already seeded), or 429.
    Idempotent guard: refuses to run twice on the same tenant to avoid duplicating demo data.
    """
    return DemoDataOrchestrator.seed(tenant_id, current_user.id)
