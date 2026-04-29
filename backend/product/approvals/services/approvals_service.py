from django.utils import timezone

from infra.common.exceptions import Conflict, NotFound
from infra.tenants.decorators import any_employee, only_manager
from product.approvals.dtos.dtos import ApprovalEventOut, ApprovalOut
from product.approvals.repositories.approvals_repository import ApprovalsRepository
from product.common.classes import ApprovalAction, ApprovalStatus


class ApprovalsService:
    @any_employee
    @staticmethod
    def ensure_report_has_no_approval(
        tenant_id: int,
        report_id: int,
        user_id: int,
    ) -> None:
        existing = ApprovalsRepository.find_by_report_id(report_id)
        if existing:
            raise Conflict(f"An approval record already exists for report {report_id}.")

    @any_employee
    @staticmethod
    def create_submitted_approval(
        tenant_id: int,
        report_id: int,
        user_id: int,
    ) -> ApprovalOut:
        ApprovalsService.ensure_report_has_no_approval(tenant_id, report_id, user_id)
        approval = ApprovalsRepository.create_approval(tenant_id, report_id, user_id)
        ApprovalsRepository.create_event(approval.id, ApprovalAction.SUBMITTED, user_id)
        return approval

    @only_manager
    @staticmethod
    def get_by_id(
        tenant_id: int,
        approval_id: int,
        user_id: int,
    ) -> ApprovalOut:
        approval = ApprovalsRepository.get_by_id(approval_id)
        if not approval:
            raise NotFound(f"Approval {approval_id} not found.")
        return approval

    @only_manager
    @staticmethod
    def get_pending_approval(
        tenant_id: int,
        approval_id: int,
        user_id: int,
    ) -> ApprovalOut:
        approval = ApprovalsRepository.get_by_id(approval_id)
        if not approval:
            raise NotFound(f"Approval {approval_id} not found.")
        if approval.status != ApprovalStatus.PENDING:
            raise Conflict(f"Cannot review an approval in status '{approval.status}'.")
        return approval

    @only_manager
    @staticmethod
    def approve_approval(
        tenant_id: int,
        approval_id: int,
        user_id: int,
    ) -> ApprovalOut:
        reviewed_at = timezone.now()
        updated = ApprovalsRepository.update_approval_status(
            approval_id,
            ApprovalStatus.APPROVED,
            user_id,
            reviewed_at,
        )
        ApprovalsRepository.create_event(approval_id, ApprovalAction.APPROVED, user_id)
        assert updated is not None
        return updated

    @only_manager
    @staticmethod
    def reject_approval(
        tenant_id: int,
        approval_id: int,
        reason: str,
        user_id: int,
    ) -> ApprovalOut:
        reviewed_at = timezone.now()
        updated = ApprovalsRepository.update_approval_status(
            approval_id,
            ApprovalStatus.REJECTED,
            user_id,
            reviewed_at,
        )
        ApprovalsRepository.create_event(
            approval_id, ApprovalAction.REJECTED, user_id, reason
        )
        assert updated is not None
        return updated

    @any_employee
    @staticmethod
    def get_approval(
        tenant_id: int,
        approval_id: int,
        user_id: int,
    ) -> ApprovalOut:
        approval = ApprovalsRepository.get_by_id(approval_id)
        if not approval or approval.tenant_id != tenant_id:
            raise NotFound(f"Approval {approval_id} not found.")
        return approval

    @any_employee
    @staticmethod
    def list_approvals(
        tenant_id: int,
        user_id: int,
        status: str | None = None,
    ) -> list[ApprovalOut]:
        return ApprovalsRepository.list_by_tenant(tenant_id, status)

    @any_employee
    @staticmethod
    def list_approval_events(
        tenant_id: int,
        approval_id: int,
        user_id: int,
    ) -> list[ApprovalEventOut]:
        if not ApprovalsRepository.get_by_id(approval_id):
            raise NotFound(f"Approval {approval_id} not found.")
        return ApprovalsRepository.list_events(approval_id)
