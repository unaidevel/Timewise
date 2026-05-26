from dataclasses import dataclass
from datetime import datetime

from infra.common.exceptions import UnprocessableEntity


@dataclass(frozen=True, slots=True)
class EntityApproval:
    reason: str

    def __post_init__(self) -> None:
        clean = self.reason.strip()
        if len(clean) > 2000:
            raise UnprocessableEntity("Reason cannot be longer than 2000 characters.")
        object.__setattr__(self, "reason", clean)


@dataclass(frozen=True, slots=True)
class UpdateApprovalStatusEntity:
    approval_id: int
    new_status: str
    user_id: int | None = None
    reviewed_at: datetime | None = None
