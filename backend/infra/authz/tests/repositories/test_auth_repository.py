from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from infra.authz.entities.auth_entities import (
    Email,
    FullName,
    UpdateUserEmailEntity,
    UpdateUserNameEntity,
    UpdateUserPasswordEntity,
)
from infra.authz.models import (
    AuthLoginAttemptModel,
    AuthLoginEventModel,
    AuthTokenModel,
    AuthUserModel,
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
            AuthService._hash_token("my-access-token"), now=timezone.now()
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

        revoked_count = AuthRepository.revoke_token(
            token_hash, revoked_at=timezone.now()
        )

        self.assertEqual(revoked_count, 1)
        self.assertIsNone(
            AuthRepository.find_valid_token(token_hash, now=timezone.now())
        )

    def test_find_token_by_refresh_hash_returns_revoked_records(self):
        user = self._create_user()
        self._create_token(user, "access-1", "refresh-1")
        AuthRepository.revoke_token(
            AuthService._hash_token("access-1"), revoked_at=timezone.now()
        )

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

        revoked = AuthRepository.revoke_token_family(
            "family-A", revoked_at=timezone.now()
        )

        self.assertEqual(revoked, 2)
        family_b = AuthRepository.find_valid_token(
            AuthService._hash_token("b1"), now=timezone.now()
        )
        self.assertIsNotNone(family_b)

    def test_revoke_oldest_active_user_sessions_caps_active(self):
        user = self._create_user()
        for index in range(4):
            self._create_token(user, f"a-{index}", f"r-{index}", family_id=f"f-{index}")

        now = timezone.now()
        active_ids = AuthRepository.list_active_session_ids(user.id, now=now)
        to_revoke = active_ids[2:]
        revoked = AuthRepository.revoke_tokens_by_ids(to_revoke, revoked_at=now)

        self.assertEqual(revoked, 2)
        self.assertEqual(AuthRepository.count_active_user_sessions(user.id, now=now), 2)

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
        AuthRepository.revoke_token(
            AuthService._hash_token("rev-1"), revoked_at=timezone.now()
        )
        # Expire one token by manipulating refresh_expires_at directly.
        AuthTokenModel.objects.filter(
            refresh_token_hash=AuthService._hash_token("ra-2")
        ).update(refresh_expires_at=timezone.now() - timedelta(days=1))

        self.assertEqual(
            AuthRepository.count_active_user_sessions(user.id, now=timezone.now()), 1
        )

    def test_find_user_by_email_returns_none_when_not_found(self):
        self.assertIsNone(AuthRepository.find_user_by_email("ghost@example.com"))

    def test_find_user_by_id_returns_user_when_found(self):
        user = self._create_user()

        found = AuthRepository.find_user_by_id(user.id)

        self.assertIsNotNone(found)
        self.assertEqual(found.id, user.id)
        self.assertEqual(found.email, user.email)

    def test_find_user_by_id_returns_none_when_not_found(self):
        self.assertIsNone(AuthRepository.find_user_by_id(99999))

    def test_find_valid_token_returns_none_for_expired_token(self):
        user = self._create_user()
        self._create_token(user, "expiring", "expiring-r")
        AuthTokenModel.objects.filter(
            token_hash=AuthService._hash_token("expiring")
        ).update(expires_at=timezone.now() - timedelta(seconds=1))

        self.assertIsNone(
            AuthRepository.find_valid_token(
                AuthService._hash_token("expiring"), now=timezone.now()
            )
        )

    def test_find_valid_token_returns_none_for_unknown_hash(self):
        self.assertIsNone(
            AuthRepository.find_valid_token("does-not-exist", now=timezone.now())
        )

    def test_find_token_by_refresh_hash_returns_none_when_unknown(self):
        self.assertIsNone(AuthRepository.find_token_by_refresh_hash("unknown"))

    def test_revoke_token_returns_zero_when_already_revoked(self):
        user = self._create_user()
        self._create_token(user, "once", "once-r")
        AuthRepository.revoke_token(
            AuthService._hash_token("once"), revoked_at=timezone.now()
        )

        revoked_again = AuthRepository.revoke_token(
            AuthService._hash_token("once"), revoked_at=timezone.now()
        )

        self.assertEqual(revoked_again, 0)

    def test_revoke_oldest_active_user_sessions_returns_zero_when_below_keep(self):
        user = self._create_user()
        self._create_token(user, "a", "ra")

        now = timezone.now()
        active_ids = AuthRepository.list_active_session_ids(user.id, now=now)
        to_revoke = active_ids[2:]
        revoked = AuthRepository.revoke_tokens_by_ids(to_revoke, revoked_at=now)

        self.assertEqual(revoked, 0)
        self.assertEqual(
            AuthRepository.count_active_user_sessions(user.id, now=timezone.now()), 1
        )

    def test_revoke_all_user_tokens_revokes_only_unrevoked(self):
        user = self._create_user()
        self._create_token(user, "t1", "r1")
        self._create_token(user, "t2", "r2")
        now = timezone.now()
        AuthRepository.revoke_token(AuthService._hash_token("t1"), revoked_at=now)

        revoked = AuthRepository.revoke_all_user_tokens(user.id, revoked_at=now)

        self.assertEqual(revoked, 1)
        self.assertEqual(AuthRepository.count_active_user_sessions(user.id, now=now), 0)

    def test_record_login_event_with_no_user_id(self):
        AuthRepository.record_login_event(
            event_type=AuthLoginEventModel.EVENT_LOGIN_FAILURE,
            email="ghost@example.com",
            client_ip="127.0.0.1",
            user_agent="pytest",
        )

        event = AuthLoginEventModel.objects.get()
        self.assertIsNone(event.user_id)
        self.assertEqual(event.email, "ghost@example.com")

    def test_update_user_name_changes_full_name(self):
        user = self._create_user()

        updated = AuthRepository.update_user_name(
            UpdateUserNameEntity(user_id=user.id, full_name=FullName("New Name"))
        )

        self.assertEqual(updated.full_name, "New Name")
        self.assertEqual(AuthUserModel.objects.get(id=user.id).full_name, "New Name")

    def test_update_user_name_rejects_wrong_entity_type(self):
        user = self._create_user()

        with self.assertRaises(TypeError):
            AuthRepository.update_user_name(
                {"user_id": user.id, "full_name": "X"}  # type: ignore[arg-type]
            )

    def test_update_user_email_changes_email(self):
        user = self._create_user()

        updated = AuthRepository.update_user_email(
            UpdateUserEmailEntity(user_id=user.id, email=Email("new@example.com"))
        )

        self.assertEqual(updated.email, "new@example.com")
        self.assertEqual(AuthUserModel.objects.get(id=user.id).email, "new@example.com")

    def test_update_user_email_raises_conflict_on_duplicate(self):
        first = self._create_user("first@example.com")
        self._create_user("second@example.com")

        with self.assertRaises(Conflict):
            AuthRepository.update_user_email(
                UpdateUserEmailEntity(
                    user_id=first.id,
                    email=Email("second@example.com"),
                )
            )

    def test_update_user_email_rejects_wrong_entity_type(self):
        user = self._create_user()

        with self.assertRaises(TypeError):
            AuthRepository.update_user_email(
                {"user_id": user.id, "email": "x@example.com"}  # type: ignore[arg-type]
            )

    def test_update_user_password_changes_hash(self):
        user = self._create_user()
        new_hash = AuthService._hash_password("AnotherPass456!")

        updated = AuthRepository.update_user_password(
            UpdateUserPasswordEntity(user_id=user.id, new_password_hash=new_hash)
        )

        self.assertEqual(updated.password_hash, new_hash)
        self.assertEqual(AuthUserModel.objects.get(id=user.id).password_hash, new_hash)

    def test_update_user_password_rejects_wrong_entity_type(self):
        user = self._create_user()

        with self.assertRaises(TypeError):
            AuthRepository.update_user_password(
                {"user_id": user.id, "new_password_hash": "x"}  # type: ignore[arg-type]
            )
