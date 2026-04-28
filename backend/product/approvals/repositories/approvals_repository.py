from datetime import datetime

from product.approvals.dtos.approval_dtos import ReportApproval, ReportApprovalEvent
from product.approvals.models import (
    TimeReportApprovalEventModel,
    TimeReportApprovalModel,
)


def _to_approval(model: TimeReportApprovalModel) -> ReportApproval:
    return ReportApproval(
        id=model.id,
        tenant_id=model.tenant_id,
        report_id=model.report_id,
        status=model.status,
        reviewer_id=model.reviewer_id,
        reviewed_at=model.reviewed_at,
        created_by_id=model.created_by_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_event(model: TimeReportApprovalEventModel) -> ReportApprovalEvent:
    return ReportApprovalEvent(
        id=model.id,
        approval_id=model.approval_id,
        action=model.action,
        actor_id=model.actor_id,
        reason=model.reason,
        actioned_at=model.actioned_at,
    )


class ApprovalsRepository:
    @staticmethod
    def create_approval(
        tenant_id: int,
        report_id: int,
        created_by_id: int,
    ) -> ReportApproval:
        model = TimeReportApprovalModel.objects.create(
            tenant_id=tenant_id,
            report_id=report_id,
            created_by_id=created_by_id,
        )
        return _to_approval(model)

    @staticmethod
    def find_by_report_id(report_id: int) -> ReportApproval | None:
        model = TimeReportApprovalModel.objects.filter(report_id=report_id).first()
        return _to_approval(model) if model else None

    @staticmethod
    def get_by_id(tenant_id: int, approval_id: int) -> ReportApproval | None:
        model = TimeReportApprovalModel.objects.filter(
            id=approval_id, tenant_id=tenant_id
        ).first()
        return _to_approval(model) if model else None

    @staticmethod
    def list_by_tenant(
        tenant_id: int,
        status: str | None = None,
    ) -> list[ReportApproval]:
        qs = TimeReportApprovalModel.objects.filter(tenant_id=tenant_id)
        if status is not None:
            qs = qs.filter(status=status)
        return [_to_approval(m) for m in qs.order_by("-created_at")]

    @staticmethod
    def update_approval_status(
        approval_id: int,
        new_status: str,
        reviewer_id: int | None = None,
        reviewed_at: datetime | None = None,
    ) -> ReportApproval | None:
        update_fields: dict = {"status": new_status}
        if reviewer_id is not None:
            update_fields["reviewer_id"] = reviewer_id
        if reviewed_at is not None:
            update_fields["reviewed_at"] = reviewed_at
        rows = TimeReportApprovalModel.objects.filter(id=approval_id).update(
            **update_fields
        )
        if rows == 0:
            return None
        model = TimeReportApprovalModel.objects.get(id=approval_id)
        return _to_approval(model)

    @staticmethod
    def create_event(
        approval_id: int,
        action: str,
        actor_id: int,
        reason: str = "",
    ) -> ReportApprovalEvent:
        model = TimeReportApprovalEventModel.objects.create(
            approval_id=approval_id,
            action=action,
            actor_id=actor_id,
            reason=reason,
        )
        return _to_event(model)

    @staticmethod
    def list_events(approval_id: int) -> list[ReportApprovalEvent]:
        return [
            _to_event(m)
            for m in TimeReportApprovalEventModel.objects.filter(
                approval_id=approval_id
            ).order_by("actioned_at")
        ]
