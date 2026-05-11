from dataclasses import dataclass, field
from typing import Any

from infra.common.exceptions import UnprocessableEntity

_MAX_ACTION_LENGTH = 100
_MAX_RESOURCE_TYPE_LENGTH = 100
_MAX_NOTES_LENGTH = 10_000


@dataclass(frozen=True, slots=True)
class AuditEventEntity:
    action: str
    resource_type: str
    resource_id: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "action",
            self._validate_short_text(self.action, "action", _MAX_ACTION_LENGTH),
        )
        object.__setattr__(
            self,
            "resource_type",
            self._validate_short_text(
                self.resource_type, "resource_type", _MAX_RESOURCE_TYPE_LENGTH
            ),
        )
        object.__setattr__(self, "notes", self._validate_notes(self.notes))
        self._validate_metadata(self.metadata)

    @staticmethod
    def _validate_short_text(value: str, field_name: str, max_length: int) -> str:
        if not isinstance(value, str):
            raise UnprocessableEntity(f"{field_name} must be a string.")
        clean = value.strip()
        if not clean:
            raise UnprocessableEntity(f"{field_name} cannot be blank.")
        if len(clean) > max_length:
            raise UnprocessableEntity(
                f"{field_name} cannot exceed {max_length} characters."
            )
        return clean

    @staticmethod
    def _validate_notes(value: str) -> str:
        if not isinstance(value, str):
            raise UnprocessableEntity("notes must be a string.")
        if len(value) > _MAX_NOTES_LENGTH:
            raise UnprocessableEntity(
                f"notes cannot exceed {_MAX_NOTES_LENGTH} characters."
            )
        return value

    @staticmethod
    def _validate_metadata(value: dict[str, Any]) -> None:
        if not isinstance(value, dict):
            raise UnprocessableEntity("metadata must be a dictionary.")
        for key in value:
            if not isinstance(key, str):
                raise UnprocessableEntity("metadata keys must be strings.")


@dataclass(frozen=True, slots=True)
class AuditEventUpdateEntity:
    """Only the free-form `notes` field is mutable on an audit event."""

    event_id: int
    notes: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "notes", AuditEventEntity._validate_notes(self.notes))
