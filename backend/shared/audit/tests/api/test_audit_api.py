import pytest
from django.test import TestCase
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from infra.authz.api import router as auth_router
from infra.authz.api.dependencies import get_current_user
from infra.authz.dtos.dtos import LoginRequest, RegisterRequest
from infra.tenants.api import router as tenants_router
from infra.tenants.dtos.dtos import TenantIn
from shared.audit.api import router as audit_router
from shared.audit.dtos.dtos import AuditEventIn, AuditEventUpdate


def build_request(
    path: str = "/api/v1/auth/login", client_host: str = "127.0.0.1"
) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": path,
            "headers": [],
            "client": (client_host, 1234),
        }
    )


def authenticate(email: str, full_name: str = "User"):
    auth_router.register(
        RegisterRequest(email=email, full_name=full_name, password="SecurePass123!")
    )
    login_response = auth_router.login_user(
        LoginRequest(email=email, password="SecurePass123!"),
        build_request(),
    )
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=login_response.access_token
    )
    return get_current_user(credentials)


def make_payload(**overrides) -> AuditEventIn:
    defaults = dict(
        action="time_report.submitted",
        resource_type="TimeReport",
        outcome="success",
        resource_id=42,
        metadata={"ip": "127.0.0.1"},
        notes="initial",
    )
    return AuditEventIn(**{**defaults, **overrides})


class AuditApiTests(TestCase):
    def setUp(self):
        self.user = authenticate(email="owner@example.com", full_name="Owner")
        self.tenant = tenants_router.create_tenant(
            TenantIn(name="Acme Corp", slug="acme"), current_user=self.user
        )

    def _record(self, **overrides):
        return audit_router.record_event(
            self.tenant.id, make_payload(**overrides), self.user
        )

    # --- record ---

    def test_record_event_returns_event(self):
        event = self._record()
        assert event.id is not None
        assert event.tenant_id == self.tenant.id
        assert event.actor_id == self.user.id
        assert event.action == "time_report.submitted"

    def test_record_event_returns_422_on_blank_action(self):
        with pytest.raises(HTTPException) as exc:
            audit_router.record_event(
                self.tenant.id,
                make_payload(action="   "),
                self.user,
            )
        assert exc.value.status_code == 422

    # --- list ---

    def test_list_events_returns_tenant_events(self):
        first = self._record(action="a")
        second = self._record(action="b")

        events = audit_router.list_events(
            self.tenant.id, self.user, None, None, None, None, None
        )

        assert [e.id for e in events] == [second.id, first.id]

    def test_list_events_filters_by_action(self):
        self._record(action="user.login")
        target = self._record(action="user.logout")

        events = audit_router.list_events(
            self.tenant.id, self.user, "user.logout", None, None, None, None
        )

        assert [e.id for e in events] == [target.id]

    def test_list_events_filters_by_resource(self):
        target = self._record(resource_type="TimeReport", resource_id=7)
        self._record(resource_type="TimeReport", resource_id=8)

        events = audit_router.list_events(
            self.tenant.id, self.user, None, "TimeReport", 7, None, None
        )

        assert [e.id for e in events] == [target.id]

    def test_list_events_filters_by_actor(self):
        target = self._record(action="mine")

        events = audit_router.list_events(
            self.tenant.id, self.user, None, None, None, self.user.id, None
        )

        assert [e.id for e in events] == [target.id]

    # --- get ---

    def test_get_event_returns_event(self):
        created = self._record()
        event = audit_router.get_event(self.tenant.id, created.id, self.user)
        assert event.id == created.id

    def test_get_event_returns_404_for_unknown_id(self):
        with pytest.raises(HTTPException) as exc:
            audit_router.get_event(self.tenant.id, 999_999, self.user)
        assert exc.value.status_code == 404

    # --- update ---

    def test_update_event_changes_notes(self):
        created = self._record(notes="initial")
        updated = audit_router.update_event(
            self.tenant.id,
            created.id,
            AuditEventUpdate(notes="patched"),
            self.user,
        )
        assert updated.notes == "patched"

    def test_update_event_returns_404_for_unknown_id(self):
        with pytest.raises(HTTPException) as exc:
            audit_router.update_event(
                self.tenant.id,
                999_999,
                AuditEventUpdate(notes="x"),
                self.user,
            )
        assert exc.value.status_code == 404

    def test_update_event_returns_403_for_employee(self):
        from infra.common.classes import MembershipRoles
        from infra.tenants.entities.tenant_entities import TenantMembershipEntity
        from infra.tenants.services.tenants_service import TenantService

        created = self._record()
        employee = authenticate(email="emp@example.com", full_name="Emp")
        TenantService.add_membership(
            tenant_id=self.tenant.id,
            user_id=employee.id,
            entity=TenantMembershipEntity(role=MembershipRoles.EMPLOYEE.value),
            invited_by_id=self.user.id,
        )

        with pytest.raises(HTTPException) as exc:
            audit_router.update_event(
                self.tenant.id,
                created.id,
                AuditEventUpdate(notes="x"),
                employee,
            )
        assert exc.value.status_code == 403

    def test_update_event_returns_422_for_oversized_notes(self):
        created = self._record()
        with pytest.raises(HTTPException) as exc:
            audit_router.update_event(
                self.tenant.id,
                created.id,
                AuditEventUpdate(notes="x" * 10_001),
                self.user,
            )
        assert exc.value.status_code == 422

    # --- delete ---

    def test_delete_event_removes_event(self):
        created = self._record()

        audit_router.delete_event(self.tenant.id, created.id, self.user)

        with pytest.raises(HTTPException) as exc:
            audit_router.get_event(self.tenant.id, created.id, self.user)
        assert exc.value.status_code == 404

    def test_delete_event_returns_404_for_unknown_id(self):
        with pytest.raises(HTTPException) as exc:
            audit_router.delete_event(self.tenant.id, 999_999, self.user)
        assert exc.value.status_code == 404
