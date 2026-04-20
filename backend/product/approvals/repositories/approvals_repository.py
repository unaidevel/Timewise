from uuid import UUID

from product.approvals.dtos.approval_dtos import Approval
from product.approvals.models import ApprovalModel


def _to_approval(approval_model: ApprovalModel) -> Approval:
    return Approval(
        id=approval_model.id,
        title=approval_model.title,
        description=approval_model.description,
        status=approval_model.status,
        created_by_user_id=approval_model.created_by_id,
        created_at=approval_model.created_at,
        updated_at=approval_model.updated_at,
    )


class ApprovalsRepository:
    @staticmethod
    def create_approval(
        title: str,
        description: str,
        created_by_user_id: UUID,
    ) -> Approval:
        approval_model = ApprovalModel.objects.create(
            title=title,
            description=description,
            created_by_id=created_by_user_id,
        )
        return _to_approval(approval_model)

    @staticmethod
    def list_approvals_for_owner(created_by_user_id: UUID) -> list[Approval]:
        approval_models = ApprovalModel.objects.filter(
            created_by_id=created_by_user_id
        ).order_by("-created_at")
        return [_to_approval(approval_model) for approval_model in approval_models]

    @staticmethod
    def find_by_id_for_owner(
        approval_id: UUID,
        created_by_user_id: UUID,
    ) -> Approval | None:
        approval_model = ApprovalModel.objects.filter(
            id=approval_id,
            created_by_id=created_by_user_id,
        ).first()
        return _to_approval(approval_model) if approval_model else None

    @staticmethod
    def update_approval(
        approval_id: UUID,
        created_by_user_id: UUID,
        *,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> Approval | None:
        approval_model = ApprovalModel.objects.filter(
            id=approval_id,
            created_by_id=created_by_user_id,
        ).first()
        if not approval_model:
            return None

        if title is not None:
            approval_model.title = title
        if description is not None:
            approval_model.description = description
        if status is not None:
            approval_model.status = status

        approval_model.save()
        approval_model.refresh_from_db()
        return _to_approval(approval_model)

    @staticmethod
    def delete_approval(approval_id: UUID, created_by_user_id: UUID) -> int:
        deleted_count, _ = ApprovalModel.objects.filter(
            id=approval_id,
            created_by_id=created_by_user_id,
        ).delete()
        return deleted_count
