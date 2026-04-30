from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from infra.authz.models import (
    AuthLoginAttemptModel,
    AuthLoginEventModel,
    AuthTokenModel,
)
from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.exceptions import Conflict


class AuthRepositoryTests(TestCase):
    def _create_user(self, email: str = "user@example.com"):
        return AuthRepository.create_user(
            email=email,
            full_name="Test User",
            password_hash=AuthService._hash_password("SecurePass123!"),
        )

    def _create_token(
        self,
        user,
        access: str,
        refresh: str,
        family_id: str = "fam-1",
        ttl_hours: int = 1,
        refresh_ttl_days: int = 7,
    ):
        return AuthRepository.create_token(
            user=user,
            family_id=family_id,
            token_hash=AuthService._hash_token(access),
            expires_at=timezone.now() + timedelta(hours=ttl_hours),
            refresh_token_hash=AuthService._hash_token(refresh),
            refresh_expires_at=timezone.now() + timedelta(days=refresh_ttl_days),
            client_ip="127.0.0.1",
            user_agent="pytest",
        )

    def test_create_and_find_user(self):
        user = self._create_user()
        found_user = AuthRepository.find_user_by_email("user@example.com")

        self.assertIsNotNone(found_user)
        self.assertEqual(found_user.id, user.id)
        self.assertEqual(found_user.email, "user@example.com")

    def test_create_user_enforces_case_insensitive_uniqueness(self):
        self._create_user()

        with self.assertRaises(Conflict):
            AuthRepository.create_user(
                email="USER@example.com",
                full_name="Test User",
                password_hash=AuthService._hash_password("SecurePass123!"),
            )

    def test_create_token_and_find_valid_token(self):
        user = self._create_user()
        self._create_token(user, "my-access-token", "my-refresh-token")

        found_token = AuthRepository.find_valid_token(
            AuthService._hash_token("my-access-token")
        )

        self.assertIsNotNone(found_token)
        self.assertEqual(found_token.user.id, user.id)
        self.assertEqual(found_token.client_ip, "127.0.0.1")
        self.assertEqual(found_token.user_agent, "pytest")
        self.assertEqual(found_token.family_id, "fam-1")

    def test_revoke_token_marks_token_as_revoked(self):
        user = self._create_user()
        self._create_token(user, "logout-token", "logout-refresh-token")
        token_hash = AuthService._hash_token("logout-token")

        revoked_count = AuthRepository.revoke_token(token_hash)

        self.assertEqual(revoked_count, 1)
        self.assertIsNone(AuthRepository.find_valid_token(token_hash))

    def test_find_token_by_refresh_hash_returns_revoked_records(self):
        user = self._create_user()
        self._create_token(user, "access-1", "refresh-1")
        AuthRepository.revoke_token(AuthService._hash_token("access-1"))

        token = AuthRepository.find_token_by_refresh_hash(
            AuthService._hash_token("refresh-1")
        )

        self.assertIsNotNone(token)
        self.assertIsNotNone(token.revoked_at)

    def test_revoke_token_family_revokes_all_unrevoked_in_family(self):
        user = self._create_user()
        self._create_token(user, "a1", "r1", family_id="family-A")
        self._create_token(user, "a2", "r2", family_id="family-A")
        self._create_token(user, "b1", "rb1", family_id="family-B")

        revoked = AuthRepository.revoke_token_family("family-A")

        self.assertEqual(revoked, 2)
        family_b = AuthRepository.find_valid_token(AuthService._hash_token("b1"))
        self.assertIsNotNone(family_b)

    def test_revoke_oldest_active_user_sessions_caps_active(self):
        user = self._create_user()
        for index in range(4):
            self._create_token(user, f"a-{index}", f"r-{index}", family_id=f"f-{index}")

        revoked = AuthRepository.revoke_oldest_active_user_sessions(user.id, keep=2)

        self.assertEqual(revoked, 2)
        self.assertEqual(AuthRepository.count_active_user_sessions(user.id), 2)

    def test_record_login_event_persists(self):
        user = self._create_user()
        AuthRepository.record_login_event(
            event_type=AuthLoginEventModel.EVENT_LOGIN_SUCCESS,
            user_id=user.id,
            email=user.email,
            client_ip="127.0.0.1",
            user_agent="pytest",
        )

        self.assertEqual(AuthLoginEventModel.objects.count(), 1)
        event = AuthLoginEventModel.objects.first()
        self.assertEqual(event.event_type, "login_success")

    def test_failed_login_attempt_helpers(self):
        now = timezone.now()
        AuthRepository.record_failed_login("user@example.com", "127.0.0.1")
        AuthRepository.record_failed_login("user@example.com", "127.0.0.1")
        stale_attempt = AuthLoginAttemptModel.objects.create(
            email="user@example.com",
            ip_address="127.0.0.2",
        )
        AuthLoginAttemptModel.objects.filter(id=stale_attempt.id).update(
            attempted_at=now - timedelta(days=40)
        )

        recent_by_email = AuthRepository.count_recent_failed_attempts_by_email(
            "user@example.com",
            now - timedelta(minutes=15),
        )
        recent_by_ip = AuthRepository.count_recent_failed_attempts_by_ip(
            "127.0.0.1",
            now - timedelta(minutes=15),
        )
        deleted_stale = AuthRepository.clear_stale_login_attempts(
            now - timedelta(days=30)
        )
        cleared_email = AuthRepository.clear_failed_logins("user@example.com")

        self.assertEqual(recent_by_email, 2)
        self.assertEqual(recent_by_ip, 2)
        self.assertEqual(deleted_stale, 1)
        self.assertEqual(cleared_email, 2)
        self.assertEqual(AuthLoginAttemptModel.objects.count(), 0)

    def test_count_active_user_sessions_excludes_revoked_and_expired(self):
        user = self._create_user()
        self._create_token(user, "active-1", "ra-1")
        self._create_token(user, "active-2", "ra-2")
        self._create_token(user, "rev-1", "rr-1")
        AuthRepository.revoke_token(AuthService._hash_token("rev-1"))
        # Expire one token by manipulating refresh_expires_at directly.
        AuthTokenModel.objects.filter(
            refresh_token_hash=AuthService._hash_token("ra-2")
        ).update(refresh_expires_at=timezone.now() - timedelta(days=1))

        self.assertEqual(AuthRepository.count_active_user_sessions(user.id), 1)
