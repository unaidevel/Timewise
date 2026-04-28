from django.utils import timezone

from infra.common.exceptions import Conflict, NotFound
from infra.tenants.decorators import any_employee, only_manager
from product.approvals.dtos.approval_dtos import ReportApproval, ReportApprovalEvent
from product.approvals.entities.approval_entities import (
    APPROVAL_ACTION_APPROVED,
    APPROVAL_ACTION_REJECTED,
    APPROVAL_ACTION_SUBMITTED,
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_REJECTED,
    ApprovalReason,
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
    ) -> ReportApproval:
        ApprovalsService.ensure_report_has_no_approval(tenant_id, report_id, user_id)
        approval = ApprovalsRepository.create_approval(
            tenant_id=tenant_id,
            report_id=report_id,
            created_by_id=user_id,
        )
        ApprovalsRepository.create_event(
            approval_id=approval.id,
            action=APPROVAL_ACTION_SUBMITTED,
            actor_id=user_id,
        )
        return approval

    @only_manager
    @staticmethod
    def get_by_id(
        tenant_id: int,
        approval_id: int,
        user_id: int,
    ) -> ReportApproval:
        approval = ApprovalsRepository.get_by_id(tenant_id, approval_id)
        if not approval or approval.tenant_id != tenant_id:
            raise NotFound(f"Approval {approval_id} not found.")
        return approval

    @only_manager
    @staticmethod
    def get_pending_approval(
        tenant_id: int,
        approval_id: int,
        user_id: int,
    ) -> ReportApproval:
        approval = ApprovalsRepository.get_by_id(approval_id)
        if not approval or approval.tenant_id != tenant_id:
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
    ) -> ReportApproval:
        ApprovalsService.get_pending_approval(tenant_id, approval_id, user_id)
        reviewed_at = timezone.now()
        updated = ApprovalsRepository.update_approval_status(
            approval_id,
            new_status=APPROVAL_STATUS_APPROVED,
            reviewer_id=user_id,
            reviewed_at=reviewed_at,
        )
        if not updated:
            raise NotFound(f"Approval {approval_id} not found.")
        ApprovalsRepository.create_event(
            approval_id=approval_id,
            action=APPROVAL_ACTION_APPROVED,
            actor_id=user_id,
        )
        return updated

    @only_manager
    @staticmethod
    def reject_approval(
        tenant_id: int,
        approval_id: int,
        reason: str,
        user_id: int,
    ) -> ReportApproval:
        clean_reason = ApprovalReason(reason).value
        approval = ApprovalsRepository.find_by_id(approval_id)
        if not approval or approval.tenant_id != tenant_id:
            raise NotFound(f"Approval {approval_id} not found.")
        if approval.status != APPROVAL_STATUS_PENDING:
            raise Conflict(f"Cannot reject an approval in status '{approval.status}'.")

        reviewed_at = timezone.now()
        updated = ApprovalsRepository.update_approval_status(
            approval_id,
            new_status=APPROVAL_STATUS_REJECTED,
            reviewer_id=user_id,
            reviewed_at=reviewed_at,
        )
        if not updated:
            raise NotFound(f"Approval {approval_id} not found.")
        ApprovalsRepository.create_event(
            approval_id=approval_id,
            action=APPROVAL_ACTION_REJECTED,
            actor_id=user_id,
            reason=clean_reason,
        )
        return updated

    @any_employee
    @staticmethod
    def get_approval(
        tenant_id: int,
        approval_id: int,
        user_id: int,
    ) -> ReportApproval:
        approval = ApprovalsRepository.find_by_id(approval_id)
        if not approval or approval.tenant_id != tenant_id:
            raise NotFound(f"Approval {approval_id} not found.")
        return approval

    @any_employee
    @staticmethod
    def list_approvals(
        tenant_id: int,
        user_id: int,
        status: str | None = None,
    ) -> list[ReportApproval]:
        return ApprovalsRepository.list_by_tenant(tenant_id, status=status)

    @any_employee
    @staticmethod
    def list_approval_events(
        tenant_id: int,
        approval_id: int,
        user_id: int,
    ) -> list[ReportApprovalEvent]:
        approval = ApprovalsRepository.find_by_id(approval_id)
        if not approval or approval.tenant_id != tenant_id:
            raise NotFound(f"Approval {approval_id} not found.")
        return ApprovalsRepository.list_events(approval_id)
