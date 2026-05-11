import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.tenants.entities.tenant_entities import TenantEntity
from infra.tenants.services.tenants_service import TenantService
from shared.audit.entities.audit_entities import (
    AuditEventEntity,
    AuditEventUpdateEntity,
)
from shared.audit.repositories.audit_repository import AuditRepository


def make_user(email: str = "owner@example.com"):
    return AuthRepository.create_user(
        email=email,
        full_name="Test User",
        password_hash=AuthService._hash_password("SecurePass123!"),
    )


def make_tenant(user_id: int, slug: str = "acme"):
    return TenantService.create(
        TenantEntity(name="Acme Corp", slug=slug), created_by_id=user_id
    )


class AuditRepositoryCreateTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)

    def _entity(self, **overrides) -> AuditEventEntity:
        defaults = dict(
            action="time_report.submitted",
            resource_type="TimeReport",
            resource_id=10,
            metadata={"foo": "bar"},
            notes="initial",
        )
        return AuditEventEntity(**{**defaults, **overrides})

    def test_create_persists_event(self):
        event = AuditRepository.create(self._entity(), self.tenant.id, self.user.id)

        assert event.id is not None
        assert event.tenant_id == self.tenant.id
        assert event.actor_id == self.user.id
        assert event.action == "time_report.submitted"
        assert event.resource_type == "TimeReport"
        assert event.resource_id == 10
        assert event.metadata == {"foo": "bar"}
        assert event.notes == "initial"
        assert event.occurred_at is not None

    def test_create_accepts_null_resource_id_and_empty_metadata(self):
        entity = AuditEventEntity(action="user.login", resource_type="AuthUser")

        event = AuditRepository.create(entity, self.tenant.id, self.user.id)

        assert event.resource_id is None
        assert event.metadata == {}
        assert event.notes == ""

    def test_create_raises_for_non_entity_payload(self):
        with pytest.raises(TypeError, match="Expected AuditEventEntity"):
            AuditRepository.create(
                "not-an-entity",  # type: ignore[arg-type]
                self.tenant.id,
                self.user.id,
            )


class AuditRepositoryReadTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        self.other_user = make_user("other@example.com")
        self.other_tenant = make_tenant(self.other_user.id, slug="other")

    def _record(
        self,
        tenant_id: int,
        actor_id: int,
        action: str = "user.login",
        resource_type: str = "AuthUser",
        resource_id: int | None = None,
    ):
        return AuditRepository.create(
            AuditEventEntity(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
            ),
            tenant_id,
            actor_id,
        )

    def test_get_by_id_returns_event(self):
        created = self._record(self.tenant.id, self.user.id)

        found = AuditRepository.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id

    def test_get_by_id_returns_none_for_unknown_id(self):
        assert AuditRepository.get_by_id(999_999) is None

    def test_list_events_orders_by_occurred_at_desc(self):
        first = self._record(self.tenant.id, self.user.id, action="a")
        second = self._record(self.tenant.id, self.user.id, action="b")

        events = AuditRepository.get_all(self.tenant.id)

        assert [e.id for e in events] == [second.id, first.id]

    def test_list_events_isolates_by_tenant(self):
        mine = self._record(self.tenant.id, self.user.id, action="mine")
        self._record(self.other_tenant.id, self.other_user.id, action="theirs")

        events = AuditRepository.get_all(self.tenant.id)

        assert [e.id for e in events] == [mine.id]

    def test_list_events_filters_by_action(self):
        self._record(self.tenant.id, self.user.id, action="user.login")
        target = self._record(self.tenant.id, self.user.id, action="user.logout")

        events = AuditRepository.get_all(self.tenant.id, "user.logout")

        assert [e.id for e in events] == [target.id]

    def test_list_events_filters_by_resource(self):
        target = self._record(
            self.tenant.id,
            self.user.id,
            resource_type="TimeReport",
            resource_id=7,
        )
        self._record(
            self.tenant.id,
            self.user.id,
            resource_type="TimeReport",
            resource_id=8,
        )

        events = AuditRepository.get_all(self.tenant.id, None, "TimeReport", 7)

        assert [e.id for e in events] == [target.id]

    def test_list_events_filters_by_actor(self):
        another = make_user("third@example.com")

        target = self._record(self.tenant.id, self.user.id, action="x")
        self._record(self.tenant.id, another.id, action="y")

        events = AuditRepository.get_all(self.tenant.id, None, None, None, self.user.id)

        assert [e.id for e in events] == [target.id]


class AuditRepositoryUpdateTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        self.event = AuditRepository.create(
            AuditEventEntity(
                action="user.login",
                resource_type="AuthUser",
                notes="initial",
            ),
            self.tenant.id,
            self.user.id,
        )

    def test_update_replaces_notes(self):
        updated = AuditRepository.update(
            AuditEventUpdateEntity(event_id=self.event.id, notes="patched")
        )

        assert updated is not None
        assert updated.id == self.event.id
        assert updated.notes == "patched"
        # Immutable fields stay the same
        assert updated.action == self.event.action
        assert updated.resource_type == self.event.resource_type
        assert updated.occurred_at == self.event.occurred_at

    def test_update_returns_none_for_unknown_event(self):
        result = AuditRepository.update(
            AuditEventUpdateEntity(event_id=999_999, notes="nope")
        )
        assert result is None

    def test_update_raises_for_non_entity_payload(self):
        with pytest.raises(TypeError, match="Expected AuditEventUpdateEntity"):
            AuditRepository.update("not-an-entity")  # type: ignore[arg-type]


class AuditRepositoryDeleteTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)

    def test_delete_by_id_returns_true_when_deleted(self):
        event = AuditRepository.create(
            AuditEventEntity(action="user.login", resource_type="AuthUser"),
            self.tenant.id,
            actor_id=self.user.id,
        )

        assert AuditRepository.delete(event.id) is True
        assert AuditRepository.get_by_id(event.id) is None

    def test_delete_by_id_returns_false_when_not_found(self):
        assert AuditRepository.delete(999_999) is False
