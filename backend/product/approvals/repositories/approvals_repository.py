from django.db.models import Sum

from product.approvals.dtos.dtos import ApprovalEventOut, ApprovalOut
from product.approvals.entities.approval_entities import UpdateApprovalStatusEntity
from product.approvals.models import (
    TimeReportApprovalEventModel,
    TimeReportApprovalModel,
)


class ApprovalsRepository:
    @staticmethod
    def create_approval(
        tenant_id: int,
        report_id: int,
        user_id: int,
    ) -> ApprovalOut:
        TimeReportApprovalModel.objects.create(
            tenant_id=tenant_id,
            report_id=report_id,
            created_by_id=user_id,
        )
        model = (
            TimeReportApprovalModel.objects.select_related(
                "report",
                "report__employee",
                "report__period",
            )
            .annotate(_total_hours=Sum("report__entries__hours"))
            .get(report_id=report_id)
        )
        return ApprovalOut.model_validate(model)

    @staticmethod
    def find_by_report_id(report_id: int) -> ApprovalOut | None:
        model = (
            TimeReportApprovalModel.objects.select_related(
                "report",
                "report__employee",
                "report__period",
            )
            .annotate(_total_hours=Sum("report__entries__hours"))
            .filter(report_id=report_id)
            .first()
        )
        return ApprovalOut.model_validate(model) if model else None

    @staticmethod
    def get_by_id(approval_id: int) -> ApprovalOut | None:
        model = (
            TimeReportApprovalModel.objects.select_related(
                "report",
                "report__employee",
                "report__period",
            )
            .annotate(_total_hours=Sum("report__entries__hours"))
            .filter(id=approval_id)
            .first()
        )
        return ApprovalOut.model_validate(model) if model else None

    @staticmethod
    def list_by_tenant(
        tenant_id: int,
        status: str | None = None,
    ) -> list[ApprovalOut]:
        qs = (
            TimeReportApprovalModel.objects.select_related(
                "report",
                "report__employee",
                "report__period",
            )
            .annotate(_total_hours=Sum("report__entries__hours"))
            .filter(tenant_id=tenant_id)
        )
        if status is not None:
            qs = qs.filter(status=status)
        return [ApprovalOut.model_validate(m) for m in qs.order_by("-created_at")]

    @staticmethod
    def update_approval_status(
        entity: UpdateApprovalStatusEntity,
    ) -> ApprovalOut | None:
        if not isinstance(entity, UpdateApprovalStatusEntity):
            raise TypeError(
                f"Expected UpdateApprovalStatusEntity, got {type(entity).__name__}"
            )
        rows = TimeReportApprovalModel.objects.filter(id=entity.approval_id).update(
            status=entity.new_status,
            reviewer_id=entity.user_id,
            reviewed_at=entity.reviewed_at,
        )
        if rows == 0:
            return None
        model = (
            TimeReportApprovalModel.objects.select_related(
                "report",
                "report__employee",
                "report__period",
            )
            .annotate(_total_hours=Sum("report__entries__hours"))
            .get(id=entity.approval_id)
        )
        return ApprovalOut.model_validate(model)

    @staticmethod
    def create_event(
        approval_id: int,
        action: str,
        user_id: int,
        reason: str = "",
    ) -> ApprovalEventOut:
        return ApprovalEventOut.model_validate(
            TimeReportApprovalEventModel.objects.create(
                approval_id=approval_id,
                action=action,
                actor_id=user_id,
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
