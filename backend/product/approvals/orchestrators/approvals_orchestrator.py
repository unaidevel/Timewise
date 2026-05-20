from django.db import transaction

from infra.common.exceptions import Conflict
from infra.tenants.decorators import any_employee, only_manager
from product.approvals.dtos.dtos import ApprovalEventOut, ApprovalOut, RejectApprovalIn
from product.approvals.entities.approval_entities import EntityApproval
from product.approvals.services.approvals_service import ApprovalsService
from product.common.classes import TimeReportStatus
from product.timekeeping.entities.timekeeping_entities import RejectReportEntity
from product.timekeeping.services.timekeeping_service import TimekeepingService
from product.workforce.services.workforce_service import Scope, WorkforceService
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
        existing = TimekeepingService.get_time_report(tenant_id, report_id, user_id)
        WorkforceService.ensure_can_access_employee(
            tenant_id, user_id, existing.employee_id
        )
        if existing.status != TimeReportStatus.DRAFT:
            raise Conflict(f"Cannot submit a report in status '{existing.status}'.")

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
                report = TimekeepingService.get_time_report(
                    tenant_id, approval.report_id, user_id
                )
                WorkforceService.ensure_can_access_employee(
                    tenant_id, user_id, report.employee_id
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
                report = TimekeepingService.get_time_report(
                    tenant_id, approval.report_id, user_id
                )
                WorkforceService.ensure_can_access_employee(
                    tenant_id, user_id, report.employee_id
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

    @any_employee
    @staticmethod
    def get_approval(tenant_id: int, approval_id: int, user_id: int) -> ApprovalOut:
        approval = ApprovalsService.get_approval(tenant_id, approval_id, user_id)
        report = TimekeepingService.get_time_report(
            tenant_id, approval.report_id, user_id
        )
        WorkforceService.ensure_can_access_employee(
            tenant_id, user_id, report.employee_id
        )
        return approval

    @any_employee
    @staticmethod
    def list_approvals(
        tenant_id: int,
        user_id: int,
        status: str | None = None,
        scope: Scope = "mine",
    ) -> list[ApprovalOut]:
        visible = WorkforceService.get_visible_employee_ids(tenant_id, user_id, scope)
        approvals = ApprovalsService.list_approvals(tenant_id, user_id, status)
        if visible is None:
            return approvals
        reports = {
            r.id: r.employee_id
            for r in TimekeepingService.list_time_reports(tenant_id, user_id)
        }
        return [a for a in approvals if reports.get(a.report_id) in visible]

    @any_employee
    @staticmethod
    def list_approval_events(
        tenant_id: int, approval_id: int, user_id: int
    ) -> list[ApprovalEventOut]:
        approval = ApprovalsService.get_approval(tenant_id, approval_id, user_id)
        report = TimekeepingService.get_time_report(
            tenant_id, approval.report_id, user_id
        )
        WorkforceService.ensure_can_access_employee(
            tenant_id, user_id, report.employee_id
        )
        return ApprovalsService.list_approval_events(tenant_id, approval_id, user_id)
