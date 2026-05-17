"""HTTP rate limiting end-to-end tests against /auth/me.

These exercise the slowapi-backed ``@limiter.limit(USER_RATE_LIMIT, ...)``
decorator on real routes — separate from the per-account login throttle in
``test_auth_api.py``, which lives in the auth service layer.
"""

from django.test import TestCase
from fastapi.security import HTTPAuthorizationCredentials
from limits import parse_many
from slowapi.errors import RateLimitExceeded
from slowapi.wrappers import Limit
from starlette.requests import Request

from infra.authz.api import router as auth_router
from infra.authz.api.dependencies import (
    get_current_user,
    get_current_user_stamped,
)
from infra.authz.dtos.auth_dtos import ClientContext
from infra.authz.services.auth_service import AuthService
from infra.common.rate_limiting import (
    limiter,
    rate_limit_exceeded_handler,
    user_or_ip_key,
)

GET_ME_FUNC_NAME = "infra.authz.api.router.get_me"


def build_request(client_host: str = "127.0.0.1") -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/auth/me",
            "headers": [],
            "client": (client_host, 1234),
        }
    )


def install_tight_limit(limit_string: str) -> list[Limit]:
    """Replace the /auth/me route limit with a tight one for the test.

    Returns the original limits so the caller can restore them.
    """
    original = list(limiter._route_limits.get(GET_ME_FUNC_NAME, []))
    items = parse_many(limit_string)
    limiter._route_limits[GET_ME_FUNC_NAME] = [
        Limit(
            limit=item,
            key_func=user_or_ip_key,
            scope=None,
            per_method=False,
            methods=None,
            error_message=None,
            exempt_when=None,
            cost=1,
            override_defaults=True,
        )
        for item in items
    ]
    return original


class RateLimitingTests(TestCase):
    def setUp(self) -> None:
        self._original_enabled = limiter.enabled
        self._original_limits = list(limiter._route_limits.get(GET_ME_FUNC_NAME, []))
        limiter.enabled = True
        limiter.reset()

    def tearDown(self) -> None:
        limiter.enabled = self._original_enabled
        limiter._route_limits[GET_ME_FUNC_NAME] = self._original_limits
        limiter.reset()

    def _make_user(self, *, email: str, full_name: str = "Test User"):
        AuthService.register_user(
            email=email, full_name=full_name, password="SecurePass123!"
        )
        session = AuthService.login(
            email=email,
            password="SecurePass123!",
            client=ClientContext(ip="127.0.0.1", user_agent="test"),
        )
        return get_current_user(
            HTTPAuthorizationCredentials(
                scheme="Bearer", credentials=session.access_token
            )
        )

    def _call_me(self, *, user, client_host: str = "127.0.0.1"):
        request = build_request(client_host=client_host)
        # Mimic the FastAPI dependency chain: get_current_user_stamped stamps
        # request.state.rate_limit_user_id, which user_or_ip_key reads.
        get_current_user_stamped(request, user)
        return auth_router.get_me(request=request, current_user=user)

    def test_returns_429_after_limit_exceeded_for_authenticated_user(self):
        install_tight_limit("3/minute")
        user = self._make_user(email="owner@example.com")

        for _ in range(3):
            self._call_me(user=user)

        with self.assertRaises(RateLimitExceeded) as exc:
            self._call_me(user=user)

        # The registered FastAPI handler converts this into a 429 JSONResponse.
        response = rate_limit_exceeded_handler(build_request(), exc.exception)
        self.assertEqual(response.status_code, 429)

    def test_per_user_isolation_buckets_dont_overlap(self):
        install_tight_limit("2/minute")
        alice = self._make_user(email="alice@example.com", full_name="Alice")
        bob = self._make_user(email="bob@example.com", full_name="Bob")

        # Alice exhausts her bucket.
        self._call_me(user=alice)
        self._call_me(user=alice)
        with self.assertRaises(RateLimitExceeded):
            self._call_me(user=alice)

        # Bob is unaffected — his per-user bucket is independent.
        self._call_me(user=bob)
        self._call_me(user=bob)
        with self.assertRaises(RateLimitExceeded):
            self._call_me(user=bob)

    def test_unauthenticated_requests_fall_back_to_per_ip_bucket(self):
        # No user stamped → user_or_ip_key returns ip:<host>.
        # Two distinct IPs should each get their own bucket.
        install_tight_limit("1/minute")

        request_a = build_request(client_host="10.0.0.1")
        request_b = build_request(client_host="10.0.0.2")

        # First call from each IP is allowed; second triggers 429.
        self.assertEqual(user_or_ip_key(request_a), "ip:10.0.0.1")
        self.assertEqual(user_or_ip_key(request_b), "ip:10.0.0.2")

        # Drive the limiter directly so we don't need a token.
        limiter._check_request_limit(request_a, auth_router.get_me, False)
        with self.assertRaises(RateLimitExceeded):
            limiter._check_request_limit(request_a, auth_router.get_me, False)

        # Independent bucket for the second IP.
        limiter._check_request_limit(request_b, auth_router.get_me, False)
        with self.assertRaises(RateLimitExceeded):
            limiter._check_request_limit(request_b, auth_router.get_me, False)

    def test_disabled_limiter_is_a_no_op(self):
        install_tight_limit("1/minute")
        limiter.enabled = False
        user = self._make_user(email="owner@example.com")

        # With the limiter disabled, well past the limit still succeeds.
        for _ in range(5):
            response = self._call_me(user=user)
            self.assertEqual(response.email, "owner@example.com")
