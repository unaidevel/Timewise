from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from infra.authz.models import AuthLoginAttemptModel
from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.exceptions import EmailAlreadyExistsError


class AuthRepositoryTests(TestCase):
    def test_create_and_find_user(self):
        user = AuthRepository.create_user(
            email="user@example.com",
            full_name="Test User",
            password_hash=AuthService._hash_password("SecurePass123!"),
        )

        found_user = AuthRepository.find_user_by_email("user@example.com")

        self.assertIsNotNone(found_user)
        self.assertEqual(found_user.id, user.id)
        self.assertEqual(found_user.email, "user@example.com")

    def test_create_user_enforces_case_insensitive_uniqueness(self):
        AuthRepository.create_user(
            email="user@example.com",
            full_name="Test User",
            password_hash=AuthService._hash_password("SecurePass123!"),
        )

        with self.assertRaises(EmailAlreadyExistsError):
            AuthRepository.create_user(
                email="USER@example.com",
                full_name="Test User",
                password_hash=AuthService._hash_password("SecurePass123!"),
            )

    def test_create_token_and_find_valid_token(self):
        user = AuthRepository.create_user(
            email="user@example.com",
            full_name="Test User",
            password_hash=AuthService._hash_password("SecurePass123!"),
        )
        raw_token = "my-access-token"
        token_hash = AuthService._hash_token(raw_token)

        AuthRepository.create_token(
            user=user,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        found_token = AuthRepository.find_valid_token(token_hash)

        self.assertIsNotNone(found_token)
        self.assertEqual(found_token.user.id, user.id)

    def test_revoke_token_marks_token_as_revoked(self):
        user = AuthRepository.create_user(
            email="user@example.com",
            full_name="Test User",
            password_hash=AuthService._hash_password("SecurePass123!"),
        )
        token_hash = AuthService._hash_token("logout-token")

        AuthRepository.create_token(
            user=user,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        revoked_count = AuthRepository.revoke_token(token_hash)

        self.assertEqual(revoked_count, 1)
        self.assertIsNone(AuthRepository.find_valid_token(token_hash))

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
