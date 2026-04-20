from django.test import TestCase
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from infra.authz.api import router as auth_router
from infra.authz.dtos.dtos import LoginRequest, RegisterRequest
from infra.authz.services.auth_service import AuthService, get_auth_security_settings


def build_request(path: str, client_host: str = "127.0.0.1") -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": path,
            "headers": [],
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
        current_user = auth_router.get_current_user(credentials)
        me_response = auth_router.get_me(current_user=current_user)

        self.assertEqual(me_response.email, "user@example.com")

        auth_router.logout_user(credentials)

        with self.assertRaises(HTTPException) as exc:
            auth_router.get_current_user(credentials)

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
