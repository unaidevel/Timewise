from product.approvals.dtos.dtos import ApprovalEventOut, ApprovalOut
from product.approvals.models import (
    TimeReportApprovalEventModel,
    TimeReportApprovalModel,
)


class ApprovalsRepository:
    @staticmethod
    def create_approval(
        tenant_id: int,
        report_id: int,
        created_by_id: int,
    ) -> ApprovalOut:
        model = TimeReportApprovalModel.objects.create(
            tenant_id=tenant_id,
            report_id=report_id,
            created_by_id=created_by_id,
        )
        return ApprovalOut.model_validate(model)

    @staticmethod
    def find_by_report_id(report_id: int) -> ApprovalOut | None:
        model = TimeReportApprovalModel.objects.filter(report_id=report_id).first()
        return ApprovalOut.model_validate(model) if model else None

    @staticmethod
    def get_by_id(approval_id: int) -> ApprovalOut | None:
        model = TimeReportApprovalModel.objects.filter(id=approval_id).first()
        return ApprovalOut.model_validate(model) if model else None

    @staticmethod
    def list_by_tenant(
        tenant_id: int,
        status: str | None = None,
    ) -> list[ApprovalOut]:
        qs = TimeReportApprovalModel.objects.filter(tenant_id=tenant_id)
        if status is not None:
            qs = qs.filter(status=status)
        return [ApprovalOut.model_validate(m) for m in qs.order_by("-created_at")]

    @staticmethod
    def update_approval_status(
        approval_id: int,
        new_status: str,
        reviewer_id: int | None = None,
        reviewed_at: object | None = None,
    ) -> ApprovalOut | None:
        rows = TimeReportApprovalModel.objects.filter(id=approval_id).update(
            status=new_status,
            reviewer_id=reviewer_id,
            reviewed_at=reviewed_at,
        )
        if rows == 0:
            return None
        model = TimeReportApprovalModel.objects.get(id=approval_id)
        return ApprovalOut.model_validate(model)

    @staticmethod
    def create_event(
        approval_id: int,
        action: str,
        actor_id: int,
        reason: str = "",
    ) -> ApprovalEventOut:
        return ApprovalEventOut.model_validate(
            TimeReportApprovalEventModel.objects.create(
                approval_id=approval_id,
                action=action,
                actor_id=actor_id,
                reason=reason,
            )
        )

    @staticmethod
    def list_events(approval_id: int) -> list[ApprovalEventOut]:
        return [
            ApprovalEventOut.model_validate(m)
            for m in TimeReportApprovalEventModel.objects.filter(
                approval_id=approval_id
            ).order_by("actioned_at")
        ]
