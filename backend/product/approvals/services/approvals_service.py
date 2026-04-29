from django.utils import timezone

from infra.common.exceptions import Conflict, NotFound
from infra.tenants.decorators import any_employee, only_manager
from product.approvals.dtos.dtos import ApprovalEventOut, ApprovalOut
from product.approvals.entities.approval_entities import (
    APPROVAL_ACTION_APPROVED,
    APPROVAL_ACTION_REJECTED,
    APPROVAL_ACTION_SUBMITTED,
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_REJECTED,
)
from product.approvals.repositories.approvals_repository import ApprovalsRepository


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
        ApprovalsRepository.create_event(
            approval.id, APPROVAL_ACTION_SUBMITTED, user_id
        )
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
        if approval.status != APPROVAL_STATUS_PENDING:
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
            APPROVAL_STATUS_APPROVED,
            user_id,
            reviewed_at,
        )
        ApprovalsRepository.create_event(approval_id, APPROVAL_ACTION_APPROVED, user_id)
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
            APPROVAL_STATUS_REJECTED,
            user_id,
            reviewed_at,
        )
        ApprovalsRepository.create_event(
            approval_id, APPROVAL_ACTION_REJECTED, user_id, reason
        )
        return updated

    @any_employee
    @staticmethod
    def get_approval(
        tenant_id: int,
        approval_id: int,
        user_id: int,
    ) -> ApprovalOut:
        approval = ApprovalsRepository.get_by_id(approval_id)
        if not approval:
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
