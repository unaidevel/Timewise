from datetime import date, datetime

from django.utils import timezone

from product.common.classes import PeriodStatus
from product.timekeeping.dtos.dtos import (
    PeriodOut,
    TimeEntryChangeHistoryOut,
    TimeEntryOut,
    TimeReportOut,
    TimeReportStatusHistoryOut,
)
from product.timekeeping.entities.timekeeping_entities import (
    PeriodEntity,
    TimeEntryEntity,
)
from product.timekeeping.models import (
    PeriodModel,
    TimeEntryChangeHistoryModel,
    TimeEntryModel,
    TimeReportModel,
    TimeReportStatusHistoryModel,
)


class TimekeepingRepository:
    @staticmethod
    def create_period(
        entity: PeriodEntity,
        tenant_id: int,
        created_by_id: int | None = None,
    ) -> PeriodOut:
        if not isinstance(entity, PeriodEntity):
            raise TypeError(f"Expected PeriodEntity, got {type(entity).__name__}")
        model = PeriodModel.objects.create(
            tenant_id=tenant_id,
            name=entity.name,
            start_date=entity.start_date,
            end_date=entity.end_date,
            status=PeriodStatus.OPEN,
            created_by_id=created_by_id,
        )
        return PeriodOut.model_validate(model)

    @staticmethod
    def get_period_by_id(period_id: int) -> PeriodOut | None:
        model = PeriodModel.objects.filter(id=period_id).first()
        return PeriodOut.model_validate(model) if model else None

    @staticmethod
    def list_periods(tenant_id: int, status: str | None = None) -> list[PeriodOut]:
        qs = PeriodModel.objects.filter(tenant_id=tenant_id)
        if status is not None:
            qs = qs.filter(status=status)
        return [PeriodOut.model_validate(m) for m in qs.order_by("-start_date")]

    @staticmethod
    def find_period_by_name(tenant_id: int, name: str) -> PeriodOut | None:
        model = PeriodModel.objects.filter(
            tenant_id=tenant_id, name__iexact=name
        ).first()
        return PeriodOut.model_validate(model) if model else None

    @staticmethod
    def find_overlapping_period(
        tenant_id: int,
        start_date: date,
        end_date: date,
        exclude_id: int | None = None,
    ) -> PeriodOut | None:
        qs = PeriodModel.objects.filter(
            tenant_id=tenant_id,
            start_date__lt=end_date,
            end_date__gt=start_date,
        )
        if exclude_id is not None:
            qs = qs.exclude(id=exclude_id)
        model = qs.first()
        return PeriodOut.model_validate(model) if model else None

    @staticmethod
    def lock_period(
        period_id: int,
        locked_by_id: int,
        locked_at: datetime,
    ) -> PeriodOut | None:
        rows = PeriodModel.objects.filter(
            id=period_id, status=PeriodStatus.OPEN
        ).update(
            status=PeriodStatus.LOCKED,
            locked_by_id=locked_by_id,
            locked_at=locked_at,
        )
        if rows == 0:
            return None
        model = PeriodModel.objects.get(id=period_id)
        return PeriodOut.model_validate(model)

    @staticmethod
    def create_time_report(
        employee_id: int,
        period_id: int,
        tenant_id: int,
        created_by_id: int | None = None,
    ) -> TimeReportOut:
        model = TimeReportModel.objects.create(
            tenant_id=tenant_id,
            employee_id=employee_id,
            period_id=period_id,
            created_by_id=created_by_id,
        )
        return TimeReportOut.model_validate(model)

    @staticmethod
    def get_time_report_by_id(report_id: int) -> TimeReportOut | None:
        model = TimeReportModel.objects.filter(id=report_id).first()
        return TimeReportOut.model_validate(model) if model else None

    @staticmethod
    def list_time_reports(
        tenant_id: int,
        period_id: int | None = None,
        employee_id: int | None = None,
    ) -> list[TimeReportOut]:
        qs = TimeReportModel.objects.filter(tenant_id=tenant_id)
        if period_id is not None:
            qs = qs.filter(period_id=period_id)
        if employee_id is not None:
            qs = qs.filter(employee_id=employee_id)
        return [TimeReportOut.model_validate(m) for m in qs.order_by("-created_at")]

    @staticmethod
    def find_report_by_employee_and_period(
        employee_id: int, period_id: int
    ) -> TimeReportOut | None:
        model = TimeReportModel.objects.filter(
            employee_id=employee_id, period_id=period_id
        ).first()
        return TimeReportOut.model_validate(model) if model else None

    @staticmethod
    def update_time_report_status(
        report_id: int,
        new_status: str,
        updated_by_id: int | None = None,
        rejection_reason: str | None = None,
        submitted_at: datetime | None = None,
        approved_at: datetime | None = None,
        rejected_at: datetime | None = None,
        locked_at: datetime | None = None,
    ) -> TimeReportOut | None:
        update_fields: dict = {"status": new_status}
        if updated_by_id is not None:
            update_fields["updated_by_id"] = updated_by_id
        if rejection_reason is not None:
            update_fields["rejection_reason"] = rejection_reason
        if submitted_at is not None:
            update_fields["submitted_at"] = submitted_at
        if approved_at is not None:
            update_fields["approved_at"] = approved_at
        if rejected_at is not None:
            update_fields["rejected_at"] = rejected_at
        if locked_at is not None:
            update_fields["locked_at"] = locked_at
        rows = TimeReportModel.objects.filter(id=report_id).update(**update_fields)
        if rows == 0:
            return None
        model = TimeReportModel.objects.get(id=report_id)
        return TimeReportOut.model_validate(model)

    @staticmethod
    def create_time_entry(
        report_id: int,
        entity: TimeEntryEntity,
        created_by_id: int | None = None,
    ) -> TimeEntryOut:
        if not isinstance(entity, TimeEntryEntity):
            raise TypeError(f"Expected TimeEntryEntity, got {type(entity).__name__}")
        model = TimeEntryModel.objects.create(
            report_id=report_id,
            date=entity.date,
            hours=entity.hours,
            start_time=entity.start_time,
            end_time=entity.end_time,
            description=entity.description,
            created_by_id=created_by_id,
        )
        return TimeEntryOut.model_validate(model)

    @staticmethod
    def get_time_entry_by_id(entry_id: int) -> TimeEntryOut | None:
        model = TimeEntryModel.objects.filter(id=entry_id).first()
        return TimeEntryOut.model_validate(model) if model else None

    @staticmethod
    def list_time_entries(report_id: int) -> list[TimeEntryOut]:
        return [
            TimeEntryOut.model_validate(m)
            for m in TimeEntryModel.objects.filter(report_id=report_id).order_by("date")
        ]

    @staticmethod
    def update_time_entry(
        entry_id: int,
        entity: TimeEntryEntity,
        updated_by_id: int | None = None,
    ) -> TimeEntryOut | None:
        rows = TimeEntryModel.objects.filter(id=entry_id).update(
            date=entity.date,
            hours=entity.hours,
            start_time=entity.start_time,
            end_time=entity.end_time,
            description=entity.description,
            updated_by_id=updated_by_id,
        )
        if rows == 0:
            return None
        model = TimeEntryModel.objects.get(id=entry_id)
        return TimeEntryOut.model_validate(model)

    @staticmethod
    def delete_time_entry(entry_id: int) -> bool:
        rows, _ = TimeEntryModel.objects.filter(id=entry_id).delete()
        return rows > 0

    @staticmethod
    def create_status_history(
        report_id: int,
        from_status: str | None,
        to_status: str,
        changed_by_id: int,
        reason: str = "",
    ) -> TimeReportStatusHistoryOut:
        model = TimeReportStatusHistoryModel.objects.create(
            report_id=report_id,
            from_status=from_status,
            to_status=to_status,
            changed_by_id=changed_by_id,
            reason=reason,
        )
        return TimeReportStatusHistoryOut.model_validate(model)

    @staticmethod
    def list_status_history(report_id: int) -> list[TimeReportStatusHistoryOut]:
        return [
            TimeReportStatusHistoryOut.model_validate(m)
            for m in TimeReportStatusHistoryModel.objects.filter(
                report_id=report_id
            ).order_by("changed_at")
        ]

    @staticmethod
    def create_entry_change_history(
        entry_id: int,
        field_name: str,
        old_value: str | None,
        new_value: str | None,
        changed_by_id: int,
    ) -> TimeEntryChangeHistoryOut:
        model = TimeEntryChangeHistoryModel.objects.create(
            entry_id=entry_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            changed_by_id=changed_by_id,
        )
        return TimeEntryChangeHistoryOut.model_validate(model)
