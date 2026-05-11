import pytest

from infra.common.exceptions import UnprocessableEntity
from shared.audit.entities.audit_entities import (
    AuditEventEntity,
    AuditEventUpdateEntity,
)


class TestAuditEventEntity:
    def test_accepts_minimal_valid_input(self):
        entity = AuditEventEntity(
            action="time_report.submitted", resource_type="TimeReport"
        )
        assert entity.action == "time_report.submitted"
        assert entity.resource_type == "TimeReport"
        assert entity.resource_id is None
        assert entity.metadata == {}
        assert entity.notes == ""

    def test_strips_whitespace_from_action(self):
        entity = AuditEventEntity(action="  user.login  ", resource_type="AuthUser")
        assert entity.action == "user.login"

    def test_strips_whitespace_from_resource_type(self):
        entity = AuditEventEntity(action="user.login", resource_type="  AuthUser  ")
        assert entity.resource_type == "AuthUser"

    def test_raises_on_blank_action(self):
        with pytest.raises(UnprocessableEntity, match="action cannot be blank"):
            AuditEventEntity(action="   ", resource_type="AuthUser")

    def test_raises_on_blank_resource_type(self):
        with pytest.raises(UnprocessableEntity, match="resource_type cannot be blank"):
            AuditEventEntity(action="user.login", resource_type="")

    def test_raises_on_action_exceeding_100_chars(self):
        with pytest.raises(UnprocessableEntity, match="action cannot exceed 100"):
            AuditEventEntity(action="x" * 101, resource_type="AuthUser")

    def test_accepts_action_exactly_100_chars(self):
        entity = AuditEventEntity(action="x" * 100, resource_type="AuthUser")
        assert len(entity.action) == 100

    def test_raises_on_resource_type_exceeding_100_chars(self):
        with pytest.raises(
            UnprocessableEntity, match="resource_type cannot exceed 100"
        ):
            AuditEventEntity(action="user.login", resource_type="x" * 101)

    def test_raises_on_non_string_action(self):
        with pytest.raises(UnprocessableEntity, match="action must be a string"):
            AuditEventEntity(action=123, resource_type="AuthUser")  # type: ignore[arg-type]

    def test_raises_on_non_string_resource_type(self):
        with pytest.raises(UnprocessableEntity, match="resource_type must be a string"):
            AuditEventEntity(action="user.login", resource_type=None)  # type: ignore[arg-type]

    def test_raises_on_notes_exceeding_10000_chars(self):
        with pytest.raises(UnprocessableEntity, match="notes cannot exceed"):
            AuditEventEntity(
                action="user.login",
                resource_type="AuthUser",
                notes="x" * 10_001,
            )

    def test_accepts_notes_exactly_10000_chars(self):
        entity = AuditEventEntity(
            action="user.login",
            resource_type="AuthUser",
            notes="x" * 10_000,
        )
        assert len(entity.notes) == 10_000

    def test_raises_on_non_string_notes(self):
        with pytest.raises(UnprocessableEntity, match="notes must be a string"):
            AuditEventEntity(
                action="user.login",
                resource_type="AuthUser",
                notes=42,  # type: ignore[arg-type]
            )

    def test_raises_on_non_dict_metadata(self):
        with pytest.raises(UnprocessableEntity, match="metadata must be a dictionary"):
            AuditEventEntity(
                action="user.login",
                resource_type="AuthUser",
                metadata=["not", "a", "dict"],  # type: ignore[arg-type]
            )

    def test_raises_on_non_string_metadata_key(self):
        with pytest.raises(UnprocessableEntity, match="metadata keys must be strings"):
            AuditEventEntity(
                action="user.login",
                resource_type="AuthUser",
                metadata={1: "value"},  # type: ignore[dict-item]
            )

    def test_accepts_arbitrary_metadata_values(self):
        entity = AuditEventEntity(
            action="user.login",
            resource_type="AuthUser",
            metadata={"ip": "127.0.0.1", "count": 3, "ok": True},
        )
        assert entity.metadata == {"ip": "127.0.0.1", "count": 3, "ok": True}

    def test_accepts_resource_id(self):
        entity = AuditEventEntity(
            action="time_report.submitted",
            resource_type="TimeReport",
            resource_id=42,
        )
        assert entity.resource_id == 42

    def test_entity_is_frozen(self):
        entity = AuditEventEntity(action="user.login", resource_type="AuthUser")
        with pytest.raises(AttributeError):
            entity.action = "other"  # type: ignore[misc]


class TestAuditEventUpdateEntity:
    def test_accepts_valid_notes(self):
        entity = AuditEventUpdateEntity(event_id=1, notes="extra context")
        assert entity.notes == "extra context"
        assert entity.event_id == 1

    def test_accepts_empty_notes(self):
        entity = AuditEventUpdateEntity(event_id=1, notes="")
        assert entity.notes == ""

    def test_raises_on_notes_exceeding_max(self):
        with pytest.raises(UnprocessableEntity, match="notes cannot exceed"):
            AuditEventUpdateEntity(event_id=1, notes="x" * 10_001)

    def test_raises_on_non_string_notes(self):
        with pytest.raises(UnprocessableEntity, match="notes must be a string"):
            AuditEventUpdateEntity(event_id=1, notes=None)  # type: ignore[arg-type]

    def test_entity_is_frozen(self):
        entity = AuditEventUpdateEntity(event_id=1, notes="hi")
        with pytest.raises(AttributeError):
            entity.notes = "other"  # type: ignore[misc]
