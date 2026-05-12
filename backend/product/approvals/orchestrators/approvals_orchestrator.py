from django.db import transaction

from infra.common.exceptions import Conflict
from infra.tenants.decorators import any_employee, only_manager
from product.approvals.dtos.dtos import ApprovalOut, RejectApprovalIn
from product.approvals.entities.approval_entities import EntityApproval
from product.approvals.services.approvals_service import ApprovalsService
from product.common.classes import TimeReportStatus
from product.timekeeping.entities.timekeeping_entities import RejectReportEntity
from product.timekeeping.services.timekeeping_service import TimekeepingService
from shared.audit.dtos.dtos import AuditEventIn
from shared.audit.services.audit_service import AuditService
from shared.audit.utils import AUDITED_FAILURES, AuditOutcome, record_failure


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

        try:
            with transaction.atomic():
                ApprovalsService.ensure_report_has_no_approval(
                    tenant_id, report_id, user_id
                )
                TimekeepingService.submit_time_report(tenant_id, report_id, user_id)
                approval = ApprovalsService.create_submitted_approval(
                    tenant_id, report_id, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="report.submitted_for_approval",
                        resource_type="TimeReport",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=report_id,
                        metadata={"approval_id": approval.id},
                    ),
                    user_id,
                )
                return approval
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="report.submitted_for_approval",
                resource_type="TimeReport",
                resource_id=report_id,
                metadata={},
                exc=exc,
            )
            raise

    @only_manager
    @staticmethod
    def approve_report(
        tenant_id: int,
        approval_id: int,
        user_id: int,
    ) -> ApprovalOut:
        try:
            with transaction.atomic():
                approval = ApprovalsService.get_pending_approval(
                    tenant_id, approval_id, user_id
                )
                TimekeepingService.approve_time_report(
                    tenant_id, approval.report_id, user_id
                )
                result = ApprovalsService.approve_approval(
                    tenant_id, approval_id, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="report.approved",
                        resource_type="TimeReport",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=approval.report_id,
                        metadata={"approval_id": approval_id},
                    ),
                    user_id,
                )
                return result
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="report.approved",
                resource_type="TimeReport",
                resource_id=None,
                metadata={"approval_id": approval_id},
                exc=exc,
            )
            raise

    @only_manager
    @staticmethod
    def reject_report(
        tenant_id: int,
        approval_id: int,
        payload: RejectApprovalIn,
        user_id: int,
    ) -> ApprovalOut:
        entity = EntityApproval(**payload.model_dump())
        try:
            with transaction.atomic():
                approval = ApprovalsService.get_pending_approval(
                    tenant_id, approval_id, user_id
                )
                TimekeepingService.reject_time_report(
                    tenant_id,
                    approval.report_id,
                    RejectReportEntity(reason=entity.reason),
                    user_id,
                )
                result = ApprovalsService.reject_approval(
                    tenant_id, approval_id, entity.reason, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="report.rejected",
                        resource_type="TimeReport",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=approval.report_id,
                        metadata={
                            "approval_id": approval_id,
                            "reason": entity.reason,
                        },
                    ),
                    user_id,
                )
                return result
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="report.rejected",
                resource_type="TimeReport",
                resource_id=None,
                metadata={"approval_id": approval_id, "reason": entity.reason},
                exc=exc,
            )
            raise
