from dataclasses import dataclass

from infra.common.exceptions import UnprocessableEntity
from product.common.classes import ApprovalAction, ApprovalStatus

APPROVAL_STATUS_PENDING = ApprovalStatus.PENDING
APPROVAL_STATUS_APPROVED = ApprovalStatus.APPROVED
APPROVAL_STATUS_REJECTED = ApprovalStatus.REJECTED
APPROVAL_STATUS_VALUES = {
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_REJECTED,
}

APPROVAL_ACTION_SUBMITTED = ApprovalAction.SUBMITTED
APPROVAL_ACTION_APPROVED = ApprovalAction.APPROVED
APPROVAL_ACTION_REJECTED = ApprovalAction.REJECTED
APPROVAL_ACTION_VALUES = {
    APPROVAL_ACTION_SUBMITTED,
    APPROVAL_ACTION_APPROVED,
    APPROVAL_ACTION_REJECTED,
}


@dataclass(frozen=True, slots=True)
class ApprovalReason:
    value: str

    def __post_init__(self) -> None:
        clean = self.value.strip()
        if len(clean) > 2000:
            raise UnprocessableEntity("Reason cannot be longer than 2000 characters.")
        object.__setattr__(self, "value", clean)
