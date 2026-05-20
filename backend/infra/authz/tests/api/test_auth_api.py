from django.test import TestCase, override_settings
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from infra.authz.api import router as auth_router
from infra.authz.api.dependencies import _resolve_client_ip, get_current_user
from infra.authz.dtos.dtos import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    UpdateEmailRequest,
    UpdateNameRequest,
    UpdatePasswordRequest,
)
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
            ),
            build_request("/api/v1/auth/register"),
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
                ),
                build_request("/api/v1/auth/register"),
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
        me_response = auth_router.get_me(
            request=build_request("/api/v1/auth/me"),
            current_user=current_user,
        )

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

    @override_settings(
        AUTH_TRUST_PROXY_HEADERS=True,
        AUTH_TRUSTED_PROXIES=["10.0.0.5"],
    )
    def test_x_real_ip_used_when_x_forwarded_for_absent(self):
        request = build_request(
            "/anything",
            client_host="10.0.0.5",
            headers=[(b"x-real-ip", b"203.0.113.9")],
        )

        self.assertEqual(_resolve_client_ip(request), "203.0.113.9")

    def test_unknown_returned_when_no_client_set(self):
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/x",
                "headers": [],
                "client": None,
            }
        )

        self.assertEqual(_resolve_client_ip(request), "unknown")


class AuthApiAdditionalTests(TestCase):
    def test_register_rejects_duplicate_email(self):
        AuthService.register_user(
            email="user@example.com",
            full_name="Test User",
            password="SecurePass123!",
        )

        with self.assertRaises(HTTPException) as exc:
            auth_router.register(
                RegisterRequest(
                    email="user@example.com",
                    full_name="Other User",
                    password="SecurePass123!",
                ),
                build_request("/api/v1/auth/register"),
            )

        self.assertEqual(exc.exception.status_code, 409)

    def test_refresh_rejects_unknown_token(self):
        with self.assertRaises(HTTPException) as exc:
            auth_router.refresh_token(
                RefreshRequest(refresh_token="ghost-refresh"),
                build_request("/api/v1/auth/refresh"),
            )

        self.assertEqual(exc.exception.status_code, 401)

    def test_logout_is_noop_without_credentials(self):
        # Calling logout with no credentials must not raise.
        auth_router.logout_user(credentials=None)

    def test_get_current_user_rejects_missing_credentials(self):
        with self.assertRaises(HTTPException) as exc:
            get_current_user(credentials=None)

        self.assertEqual(exc.exception.status_code, 401)


class ProfileUpdateApiTests(TestCase):
    def setUp(self):
        AuthService.register_user(
            email="user@example.com",
            full_name="Original Name",
            password="SecurePass123!",
        )
        self.login_response = auth_router.login_user(
            LoginRequest(email="user@example.com", password="SecurePass123!"),
            build_request("/api/v1/auth/login"),
        )
        self.credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=self.login_response.access_token,
        )
        self.current_user = get_current_user(self.credentials)

    def test_update_my_name_changes_full_name(self):
        response = auth_router.update_my_name(
            UpdateNameRequest(full_name="  New Name  "),
            current_user=self.current_user,
            request=build_request("/api/v1/auth/me/name"),
        )

        self.assertEqual(response.full_name, "New Name")
        self.assertEqual(response.email, "user@example.com")

    def test_update_my_name_rejects_blank(self):
        with self.assertRaises(HTTPException) as exc:
            auth_router.update_my_name(
                UpdateNameRequest(full_name="   "),
                current_user=self.current_user,
                request=build_request("/api/v1/auth/me/name"),
            )

        self.assertEqual(exc.exception.status_code, 422)

    def test_update_my_email_changes_email(self):
        response = auth_router.update_my_email(
            UpdateEmailRequest(email="NEW@example.com"),
            current_user=self.current_user,
            request=build_request("/api/v1/auth/me/email"),
        )

        self.assertEqual(response.email, "new@example.com")

    def test_update_my_email_rejects_invalid(self):
        with self.assertRaises(HTTPException) as exc:
            auth_router.update_my_email(
                UpdateEmailRequest(email="not-an-email"),
                current_user=self.current_user,
                request=build_request("/api/v1/auth/me/email"),
            )

        self.assertEqual(exc.exception.status_code, 422)

    def test_update_my_email_returns_409_on_duplicate(self):
        AuthService.register_user(
            email="taken@example.com",
            full_name="Other",
            password="SecurePass123!",
        )

        with self.assertRaises(HTTPException) as exc:
            auth_router.update_my_email(
                UpdateEmailRequest(email="taken@example.com"),
                current_user=self.current_user,
                request=build_request("/api/v1/auth/me/email"),
            )

        self.assertEqual(exc.exception.status_code, 409)

    def test_update_my_password_returns_new_session(self):
        response = auth_router.update_my_password(
            UpdatePasswordRequest(
                current_password="SecurePass123!",
                new_password="AnotherPass456!",
            ),
            current_user=self.current_user,
            request=build_request("/api/v1/auth/me/password"),
        )

        self.assertNotEqual(response.access_token, self.login_response.access_token)
        self.assertNotEqual(response.refresh_token, self.login_response.refresh_token)
        self.assertEqual(response.user.email, "user@example.com")

    def test_update_my_password_revokes_existing_sessions(self):
        auth_router.update_my_password(
            UpdatePasswordRequest(
                current_password="SecurePass123!",
                new_password="AnotherPass456!",
            ),
            current_user=self.current_user,
            request=build_request("/api/v1/auth/me/password"),
        )

        # Old access token must no longer authenticate.
        with self.assertRaises(HTTPException) as exc:
            get_current_user(self.credentials)
        self.assertEqual(exc.exception.status_code, 401)

    def test_update_my_password_rejects_wrong_current_password(self):
        with self.assertRaises(HTTPException) as exc:
            auth_router.update_my_password(
                UpdatePasswordRequest(
                    current_password="not-the-right-password",
                    new_password="AnotherPass456!",
                ),
                current_user=self.current_user,
                request=build_request("/api/v1/auth/me/password"),
            )

        self.assertEqual(exc.exception.status_code, 401)

    def test_update_my_password_rejects_weak_new_password(self):
        with self.assertRaises(HTTPException) as exc:
            auth_router.update_my_password(
                UpdatePasswordRequest(
                    current_password="SecurePass123!",
                    new_password="password",
                ),
                current_user=self.current_user,
                request=build_request("/api/v1/auth/me/password"),
            )

        self.assertEqual(exc.exception.status_code, 422)

    def test_update_my_password_new_credentials_work_for_login(self):
        auth_router.update_my_password(
            UpdatePasswordRequest(
                current_password="SecurePass123!",
                new_password="AnotherPass456!",
            ),
            current_user=self.current_user,
            request=build_request("/api/v1/auth/me/password"),
        )

        new_login = auth_router.login_user(
            LoginRequest(email="user@example.com", password="AnotherPass456!"),
            build_request("/api/v1/auth/login"),
        )

        self.assertEqual(new_login.user.email, "user@example.com")
