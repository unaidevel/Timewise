from product.approvals.dtos.approval_dtos import Approval
from product.approvals.dtos.dtos import ApprovalResponse


def to_approval_response(approval: Approval) -> ApprovalResponse:
    return ApprovalResponse(
        id=approval.id,
        title=approval.title,
        description=approval.description,
        status=approval.status,
        created_by_user_id=approval.created_by_user_id,
        created_at=approval.created_at,
        updated_at=approval.updated_at,
    )
