from product.approvals.dtos.approval_dtos import Approval
from product.approvals.entities.approval_entities import (
    ApprovalDescription,
    ApprovalStatus,
    ApprovalTitle,
)
from product.approvals.exceptions import (
    ApprovalNotFoundError,
    InvalidApprovalValueError,
)
from product.approvals.repositories.approvals_repository import ApprovalsRepository


class ApprovalsService:
    @staticmethod
    def create_approval(
        title: str,
        description: str,
        created_by_user_id: int,
    ) -> Approval:
        return ApprovalsRepository.create_approval(
            title=ApprovalTitle(title).value,
            description=ApprovalDescription(description).value,
            created_by_user_id=created_by_user_id,
        )

    @staticmethod
    def list_approvals(created_by_user_id: int) -> list[Approval]:
        return ApprovalsRepository.list_approvals_for_owner(created_by_user_id)

    @staticmethod
    def get_approval(approval_id: int, created_by_user_id: int) -> Approval:
        approval = ApprovalsRepository.find_by_id_for_owner(
            approval_id,
            created_by_user_id,
        )
        if not approval:
            raise ApprovalNotFoundError("Approval not found.")

        return approval

    @staticmethod
    def update_approval(
        approval_id: int,
        created_by_user_id: int,
        *,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> Approval:
        if title is None and description is None and status is None:
            raise InvalidApprovalValueError(
                "At least one field must be provided."
            )

        updated_approval = ApprovalsRepository.update_approval(
            approval_id,
            created_by_user_id,
            title=ApprovalTitle(title).value if title is not None else None,
            description=(
                ApprovalDescription(description).value
                if description is not None
                else None
            ),
            status=ApprovalStatus(status).value if status is not None else None,
        )
        if not updated_approval:
            raise ApprovalNotFoundError("Approval not found.")

        return updated_approval

    @staticmethod
    def delete_approval(approval_id: int, created_by_user_id: int) -> None:
        deleted_count = ApprovalsRepository.delete_approval(
            approval_id,
            created_by_user_id,
        )
        if deleted_count == 0:
            raise ApprovalNotFoundError("Approval not found.")
