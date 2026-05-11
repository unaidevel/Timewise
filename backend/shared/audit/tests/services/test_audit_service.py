import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.common.exceptions import Forbidden, NotFound, UnprocessableEntity
from infra.tenants.entities.tenant_entities import TenantEntity, TenantMembershipEntity
from infra.tenants.services.tenants_service import TenantService
from shared.audit.dtos.dtos import AuditEventIn, AuditEventUpdate
from shared.audit.services.audit_service import AuditService as AuditAppService


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


def add_member(tenant_id: int, user_id: int, role: MembershipRoles):
    TenantService.add_membership(
        tenant_id=tenant_id,
        user_id=user_id,
        entity=TenantMembershipEntity(role=role.value),
        invited_by_id=None,
    )


def make_payload(**overrides) -> AuditEventIn:
    defaults = dict(
        action="time_report.submitted",
        resource_type="TimeReport",
        resource_id=42,
        metadata={"ip": "127.0.0.1"},
        notes="initial",
    )
    return AuditEventIn(**{**defaults, **overrides})


class RecordEventTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        add_member(self.tenant.id, self.user.id, MembershipRoles.OWNER)

    def test_record_event_persists_and_returns_event(self):
        event = AuditAppService.create(self.tenant.id, make_payload(), self.user.id)

        assert event.id is not None
        assert event.tenant_id == self.tenant.id
        assert event.actor_id == self.user.id
        assert event.action == "time_report.submitted"
        assert event.metadata == {"ip": "127.0.0.1"}
        assert event.notes == "initial"

    def test_record_event_strips_action_whitespace(self):
        event = AuditAppService.create(
            self.tenant.id,
            make_payload(action="  user.login  "),
            self.user.id,
        )
        assert event.action == "user.login"

    def test_record_event_raises_on_blank_action(self):
        with pytest.raises(UnprocessableEntity, match="action cannot be blank"):
            AuditAppService.create(
                self.tenant.id,
                make_payload(action="   "),
                self.user.id,
            )

    def test_record_event_allows_any_employee(self):
        employee = make_user("emp@example.com")
        add_member(self.tenant.id, employee.id, MembershipRoles.EMPLOYEE)

        event = AuditAppService.create(self.tenant.id, make_payload(), employee.id)
        assert event.actor_id == employee.id

    def test_record_event_forbidden_for_non_member(self):
        outsider = make_user("outsider@example.com")
        with pytest.raises(Forbidden):
            AuditAppService.create(self.tenant.id, make_payload(), outsider.id)


class GetEventTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        add_member(self.tenant.id, self.user.id, MembershipRoles.OWNER)
        self.event = AuditAppService.create(
            self.tenant.id, make_payload(), self.user.id
        )

    def test_get_event_returns_event(self):
        event = AuditAppService.get_by_id(self.tenant.id, self.event.id, self.user.id)
        assert event.id == self.event.id

    def test_get_event_raises_not_found_for_unknown_id(self):
        with pytest.raises(NotFound):
            AuditAppService.get_by_id(self.tenant.id, 999_999, self.user.id)

    def test_get_event_raises_not_found_for_other_tenant(self):
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, slug="other")
        add_member(other_tenant.id, other_user.id, MembershipRoles.OWNER)
        foreign_event = AuditAppService.create(
            other_tenant.id, make_payload(), other_user.id
        )

        with pytest.raises(NotFound):
            AuditAppService.get_by_id(self.tenant.id, foreign_event.id, self.user.id)

    def test_get_event_forbidden_for_non_member(self):
        outsider = make_user("outsider@example.com")
        with pytest.raises(Forbidden):
            AuditAppService.get_by_id(self.tenant.id, self.event.id, outsider.id)


class ListEventsTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        add_member(self.tenant.id, self.user.id, MembershipRoles.OWNER)

        self.other_user = make_user("other@example.com")
        self.other_tenant = make_tenant(self.other_user.id, slug="other")
        add_member(self.other_tenant.id, self.other_user.id, MembershipRoles.OWNER)

    def _record(self, tenant_id: int, actor_id: int, **overrides):
        return AuditAppService.create(tenant_id, make_payload(**overrides), actor_id)

    def test_list_events_returns_only_tenant_events(self):
        mine = self._record(self.tenant.id, self.user.id, action="mine")
        self._record(self.other_tenant.id, self.other_user.id, action="theirs")

        events = AuditAppService.get_all(self.tenant.id, self.user.id)

        assert [e.id for e in events] == [mine.id]

    def test_list_events_filters_by_action(self):
        self._record(self.tenant.id, self.user.id, action="user.login")
        target = self._record(self.tenant.id, self.user.id, action="user.logout")

        events = AuditAppService.get_all(self.tenant.id, self.user.id, "user.logout")

        assert [e.id for e in events] == [target.id]

    def test_list_events_filters_by_resource(self):
        target = self._record(
            self.tenant.id,
            self.user.id,
            resource_type="TimeReport",
            resource_id=99,
        )
        self._record(
            self.tenant.id,
            self.user.id,
            resource_type="TimeReport",
            resource_id=100,
        )

        events = AuditAppService.get_all(
            self.tenant.id, self.user.id, None, "TimeReport", 99
        )

        assert [e.id for e in events] == [target.id]

    def test_list_events_filters_by_actor(self):
        another = make_user("third@example.com")
        add_member(self.tenant.id, another.id, MembershipRoles.EMPLOYEE)

        target = self._record(self.tenant.id, self.user.id, action="a")
        self._record(self.tenant.id, another.id, action="b")

        events = AuditAppService.get_all(
            self.tenant.id, self.user.id, None, None, None, self.user.id
        )

        assert [e.id for e in events] == [target.id]

    def test_list_events_forbidden_for_non_member(self):
        outsider = make_user("outsider@example.com")
        with pytest.raises(Forbidden):
            AuditAppService.get_all(self.tenant.id, outsider.id)


class UpdateEventTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        add_member(self.tenant.id, self.user.id, MembershipRoles.OWNER)
        self.event = AuditAppService.create(
            self.tenant.id, make_payload(notes="initial"), self.user.id
        )

    def test_update_event_changes_notes(self):
        updated = AuditAppService.update(
            self.tenant.id,
            self.event.id,
            AuditEventUpdate(notes="patched"),
            self.user.id,
        )

        assert updated.notes == "patched"
        assert updated.action == self.event.action
        assert updated.occurred_at == self.event.occurred_at

    def test_update_event_raises_not_found_for_unknown_id(self):
        with pytest.raises(NotFound):
            AuditAppService.update(
                self.tenant.id,
                999_999,
                AuditEventUpdate(notes="x"),
                self.user.id,
            )

    def test_update_event_raises_not_found_for_other_tenant(self):
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, slug="other")
        add_member(other_tenant.id, other_user.id, MembershipRoles.OWNER)
        foreign_event = AuditAppService.create(
            other_tenant.id, make_payload(), other_user.id
        )

        with pytest.raises(NotFound):
            AuditAppService.update(
                self.tenant.id,
                foreign_event.id,
                AuditEventUpdate(notes="x"),
                self.user.id,
            )

    def test_update_event_forbidden_for_employee(self):
        employee = make_user("emp@example.com")
        add_member(self.tenant.id, employee.id, MembershipRoles.EMPLOYEE)

        with pytest.raises(Forbidden):
            AuditAppService.update(
                self.tenant.id,
                self.event.id,
                AuditEventUpdate(notes="x"),
                employee.id,
            )

    def test_update_event_raises_unprocessable_for_oversized_notes(self):
        with pytest.raises(UnprocessableEntity, match="notes cannot exceed"):
            AuditAppService.update(
                self.tenant.id,
                self.event.id,
                AuditEventUpdate(notes="x" * 10_001),
                self.user.id,
            )


class DeleteEventTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.tenant = make_tenant(self.user.id)
        add_member(self.tenant.id, self.user.id, MembershipRoles.OWNER)
        self.event = AuditAppService.create(
            self.tenant.id, make_payload(), self.user.id
        )

    def test_delete_event_removes_event(self):
        AuditAppService.delete(self.tenant.id, self.event.id, self.user.id)

        with pytest.raises(NotFound):
            AuditAppService.get_by_id(self.tenant.id, self.event.id, self.user.id)

    def test_delete_event_raises_not_found_for_unknown_id(self):
        with pytest.raises(NotFound):
            AuditAppService.delete(self.tenant.id, 999_999, self.user.id)

    def test_delete_event_raises_not_found_for_other_tenant(self):
        other_user = make_user("other@example.com")
        other_tenant = make_tenant(other_user.id, slug="other")
        add_member(other_tenant.id, other_user.id, MembershipRoles.OWNER)
        foreign_event = AuditAppService.create(
            other_tenant.id, make_payload(), other_user.id
        )

        with pytest.raises(NotFound):
            AuditAppService.delete(self.tenant.id, foreign_event.id, self.user.id)

    def test_delete_event_forbidden_for_employee(self):
        employee = make_user("emp@example.com")
        add_member(self.tenant.id, employee.id, MembershipRoles.EMPLOYEE)

        with pytest.raises(Forbidden):
            AuditAppService.delete(self.tenant.id, self.event.id, employee.id)
