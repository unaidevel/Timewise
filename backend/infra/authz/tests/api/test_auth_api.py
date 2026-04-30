from django.test import TestCase, override_settings
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from infra.authz.api import router as auth_router
from infra.authz.api.dependencies import _resolve_client_ip, get_current_user
from infra.authz.dtos.dtos import LoginRequest, RefreshRequest, RegisterRequest
from infra.authz.services.auth_service import AuthService, get_auth_security_settings


def build_request(
    path: str,
    client_host: str = "127.0.0.1",
    headers: list[tuple[bytes, bytes]] | None = None,
) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": path,
            "headers": headers or [],
            "client": (client_host, 1234),
        }
    )


class AuthApiTests(TestCase):
    def test_register_creates_user(self):
        response = auth_router.register(
            RegisterRequest(
                email="USER@example.com",
                full_name="  Test User  ",
                password="SecurePass123!",
            )
        )

        self.assertEqual(response.email, "user@example.com")
        self.assertEqual(response.full_name, "Test User")

    def test_register_rejects_weak_password(self):
        with self.assertRaises(HTTPException) as exc:
            auth_router.register(
                RegisterRequest(
                    email="user@example.com",
                    full_name="Test User",
                    password="password",
                )
            )

        self.assertEqual(exc.exception.status_code, 422)
        self.assertIn("common", " ".join(exc.exception.detail).lower())

    def test_login_me_and_logout_flow(self):
        AuthService.register_user(
            email="user@example.com",
            full_name="Test User",
            password="SecurePass123!",
        )

        login_response = auth_router.login_user(
            LoginRequest(email="user@example.com", password="SecurePass123!"),
            build_request("/api/v1/auth/login"),
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=login_response.access_token,
        )
        current_user = get_current_user(credentials)
        me_response = auth_router.get_me(current_user=current_user)

        self.assertEqual(me_response.email, "user@example.com")

        auth_router.logout_user(credentials)

        with self.assertRaises(HTTPException) as exc:
            get_current_user(credentials)

        self.assertEqual(exc.exception.status_code, 401)

    def test_login_rate_limit_returns_429(self):
        auth_settings = get_auth_security_settings()
        AuthService.register_user(
            email="user@example.com",
            full_name="Test User",
            password="SecurePass123!",
        )

        for _ in range(auth_settings.max_failed_attempts_per_account):
            with self.assertRaises(HTTPException) as exc:
                auth_router.login_user(
                    LoginRequest(
                        email="user@example.com",
                        password="wrong-password",
                    ),
                    build_request("/api/v1/auth/login"),
                )
            self.assertEqual(exc.exception.status_code, 401)

        with self.assertRaises(HTTPException) as exc:
            auth_router.login_user(
                LoginRequest(
                    email="user@example.com",
                    password="wrong-password",
                ),
                build_request("/api/v1/auth/login"),
            )

        self.assertEqual(exc.exception.status_code, 429)

    def test_refresh_rotates_and_invalidates_old_token(self):
        AuthService.register_user(
            email="user@example.com",
            full_name="Test User",
            password="SecurePass123!",
        )

        login_response = auth_router.login_user(
            LoginRequest(email="user@example.com", password="SecurePass123!"),
            build_request("/api/v1/auth/login"),
        )

        rotated = auth_router.refresh_token(
            RefreshRequest(refresh_token=login_response.refresh_token),
            build_request("/api/v1/auth/refresh"),
        )

        self.assertNotEqual(rotated.access_token, login_response.access_token)
        self.assertNotEqual(rotated.refresh_token, login_response.refresh_token)

        old_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=login_response.access_token,
        )
        with self.assertRaises(HTTPException):
            get_current_user(old_credentials)

    def test_refresh_reuse_revokes_entire_family(self):
        AuthService.register_user(
            email="user@example.com",
            full_name="Test User",
            password="SecurePass123!",
        )

        login_response = auth_router.login_user(
            LoginRequest(email="user@example.com", password="SecurePass123!"),
            build_request("/api/v1/auth/login"),
        )

        rotated = auth_router.refresh_token(
            RefreshRequest(refresh_token=login_response.refresh_token),
            build_request("/api/v1/auth/refresh"),
        )

        with self.assertRaises(HTTPException) as exc:
            auth_router.refresh_token(
                RefreshRequest(refresh_token=login_response.refresh_token),
                build_request("/api/v1/auth/refresh"),
            )
        self.assertEqual(exc.exception.status_code, 401)

        rotated_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=rotated.access_token,
        )
        with self.assertRaises(HTTPException):
            get_current_user(rotated_credentials)


class ClientIpResolutionTests(TestCase):
    def test_direct_ip_when_proxy_trust_disabled(self):
        request = build_request(
            "/anything",
            client_host="10.0.0.5",
            headers=[(b"x-forwarded-for", b"203.0.113.7, 10.0.0.5")],
        )

        self.assertEqual(_resolve_client_ip(request), "10.0.0.5")

    @override_settings(
        AUTH_TRUST_PROXY_HEADERS=True,
        AUTH_TRUSTED_PROXIES=["10.0.0.5"],
    )
    def test_x_forwarded_for_used_when_request_comes_from_trusted_proxy(self):
        request = build_request(
            "/anything",
            client_host="10.0.0.5",
            headers=[(b"x-forwarded-for", b"203.0.113.7, 10.0.0.5")],
        )

        self.assertEqual(_resolve_client_ip(request), "203.0.113.7")

    @override_settings(
        AUTH_TRUST_PROXY_HEADERS=True,
        AUTH_TRUSTED_PROXIES=["10.0.0.5"],
    )
    def test_x_forwarded_for_ignored_for_untrusted_origin(self):
        request = build_request(
            "/anything",
            client_host="198.51.100.1",
            headers=[(b"x-forwarded-for", b"203.0.113.7")],
        )

        self.assertEqual(_resolve_client_ip(request), "198.51.100.1")
