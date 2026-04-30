from django.db import transaction

from infra.common.exceptions import Conflict
from infra.tenants.decorators import any_employee, only_manager
from product.approvals.dtos.dtos import ApprovalOut, RejectApprovalIn
from product.approvals.entities.approval_entities import EntityApproval
from product.approvals.services.approvals_service import ApprovalsService
from product.common.classes import TimeReportStatus
from product.timekeeping.dtos.dtos import RejectReportRequest
from product.timekeeping.services.timekeeping_service import TimekeepingService


class ApprovalsOrchestrator:
    @any_employee
    @staticmethod
    def submit_report_for_approval(
        tenant_id: int,
        report_id: int,
        user_id: int,
    ) -> ApprovalOut:
        report = TimekeepingService.get_report_status(tenant_id, report_id, user_id)
        if report != TimeReportStatus.DRAFT:
            raise Conflict(f"Cannot submit a report in status '{report}'.")

        entries = TimekeepingService.list_time_entries(tenant_id, report_id, user_id)
        if not entries:
            raise Conflict("Cannot submit an empty report.")

        with transaction.atomic():
            ApprovalsService.ensure_report_has_no_approval(
                tenant_id, report_id, user_id
            )
            TimekeepingService.submit_time_report(tenant_id, report_id, user_id)
            return ApprovalsService.create_submitted_approval(
                tenant_id, report_id, user_id
            )

    @only_manager
    @staticmethod
    def approve_report(
        tenant_id: int,
        approval_id: int,
        user_id: int,
    ) -> ApprovalOut:

        with transaction.atomic():
            approval = ApprovalsService.get_pending_approval(
                tenant_id, approval_id, user_id
            )
            TimekeepingService.approve_time_report(
                tenant_id, approval.report_id, user_id
            )
            return ApprovalsService.approve_approval(tenant_id, approval_id, user_id)

    @only_manager
    @staticmethod
    def reject_report(
        tenant_id: int,
        approval_id: int,
        payload: RejectApprovalIn,
        user_id: int,
    ) -> ApprovalOut:
        entity = EntityApproval(**payload.model_dump())
        approval = ApprovalsService.get_pending_approval(
            tenant_id, approval_id, user_id
        )

        with transaction.atomic():
            TimekeepingService.reject_time_report(
                tenant_id,
                approval.report_id,
                RejectReportRequest(reason=entity.reason),
                user_id,
            )
            return ApprovalsService.reject_approval(
                tenant_id, approval_id, entity.reason, user_id
            )
