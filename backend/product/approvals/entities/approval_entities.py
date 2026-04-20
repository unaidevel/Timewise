from dataclasses import dataclass

from product.approvals.exceptions import InvalidApprovalValueError

APPROVAL_STATUS_PENDING = "pending"
APPROVAL_STATUS_APPROVED = "approved"
APPROVAL_STATUS_REJECTED = "rejected"
APPROVAL_STATUS_VALUES = {
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_REJECTED,
}


@dataclass(frozen=True, slots=True)
class ApprovalTitle:
    value: str

    def __post_init__(self) -> None:
        clean_title = self.value.strip()
        if not clean_title:
            raise InvalidApprovalValueError("Approval title cannot be blank.")
        if len(clean_title) > 200:
            raise InvalidApprovalValueError(
                "Approval title cannot be longer than 200 characters."
            )

        object.__setattr__(self, "value", clean_title)


@dataclass(frozen=True, slots=True)
class ApprovalDescription:
    value: str

    def __post_init__(self) -> None:
        clean_description = self.value.strip()
        if len(clean_description) > 2000:
            raise InvalidApprovalValueError(
                "Approval description cannot be longer than 2000 characters."
            )

        object.__setattr__(self, "value", clean_description)


@dataclass(frozen=True, slots=True)
class ApprovalStatus:
    value: str

    def __post_init__(self) -> None:
        normalized_status = self.value.strip().lower()
        if normalized_status not in APPROVAL_STATUS_VALUES:
            raise InvalidApprovalValueError(
                "Approval status must be pending, approved or rejected."
            )

        object.__setattr__(self, "value", normalized_status)
