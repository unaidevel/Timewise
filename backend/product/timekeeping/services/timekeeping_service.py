from django.utils import timezone

from infra.common.exceptions import Conflict, NotFound, UnprocessableEntity
from infra.tenants.decorators import any_employee, only_admin, only_manager
from product.common.classes import PeriodStatus, TimeReportStatus
from product.timekeeping.dtos.dtos import (
    PeriodIn,
    PeriodOut,
    RejectReportRequest,
    TimeEntryIn,
    TimeEntryOut,
    TimeEntryUpdate,
    TimeReportIn,
    TimeReportOut,
    TimeReportStatusHistoryOut,
)
from product.timekeeping.entities.timekeeping_entities import (
    PeriodEntity,
    TimeEntryEntity,
)
from product.timekeeping.repositories.timekeeping_repository import (
    TimekeepingRepository,
)


class TimekeepingService:
    @only_admin
    @staticmethod
    def create_period(
        tenant_id: int,
        payload: PeriodIn,
        user_id: int,
    ) -> PeriodOut:
        entity = PeriodEntity(
            name=payload.name,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
        existing = TimekeepingRepository.find_period_by_name(tenant_id, entity.name)
        if existing:
            raise Conflict(
                f"A period named '{existing.name}' already exists in this tenant."
            )
        overlapping = TimekeepingRepository.find_overlapping_period(
            tenant_id, entity.start_date, entity.end_date
        )
        if overlapping:
            raise Conflict(
                f"Period '{overlapping.name}' overlaps with the requested dates."
            )
        return TimekeepingRepository.create_period(
            entity, tenant_id, created_by_id=user_id
        )

    @any_employee
    @staticmethod
    def get_period(tenant_id: int, period_id: int, user_id: int) -> PeriodOut:
        period = TimekeepingRepository.get_period_by_id(period_id)
        if not period or period.tenant_id != tenant_id:
            raise NotFound(f"Period {period_id} not found.")
        return period

    @any_employee
    @staticmethod
    def list_periods(
        tenant_id: int, user_id: int, status: str | None = None
    ) -> list[PeriodOut]:
        return TimekeepingRepository.list_periods(tenant_id, status=status)

    @only_admin
    @staticmethod
    def lock_period(tenant_id: int, period_id: int, user_id: int) -> PeriodOut:
        period = TimekeepingRepository.get_period_by_id(period_id)
        if not period or period.tenant_id != tenant_id:
            raise NotFound(f"Period {period_id} not found.")
        if period.status == PeriodStatus.LOCKED:
            raise Conflict(f"Period {period_id} is already locked.")
        result = TimekeepingRepository.lock_period(
            period_id, locked_by_id=user_id, locked_at=timezone.now()
        )
        if not result:
            raise Conflict(f"Period {period_id} could not be locked.")
        return result

    @any_employee
    @staticmethod
    def create_time_report(
        tenant_id: int,
        period_id: int,
        payload: TimeReportIn,
        user_id: int,
    ) -> TimeReportOut:
        period = TimekeepingRepository.get_period_by_id(period_id)
        if not period or period.tenant_id != tenant_id:
            raise NotFound(f"Period {period_id} not found.")
        if period.status == PeriodStatus.LOCKED:
            raise Conflict(f"Period {period_id} is locked. Cannot create reports.")
        existing = TimekeepingRepository.find_report_by_employee_and_period(
            payload.employee_id, period_id
        )
        if existing:
            raise Conflict(
                f"Employee {payload.employee_id} already has a report for period {period_id}."
            )
        return TimekeepingRepository.create_time_report(
            employee_id=payload.employee_id,
            period_id=period_id,
            tenant_id=tenant_id,
            created_by_id=user_id,
        )

    @any_employee
    @staticmethod
    def get_time_report(tenant_id: int, report_id: int, user_id: int) -> TimeReportOut:
        report = TimekeepingRepository.get_time_report_by_id(report_id)
        if not report or report.tenant_id != tenant_id:
            raise NotFound(f"Time report {report_id} not found.")
        return report

    @any_employee
    @staticmethod
    def list_time_reports(
        tenant_id: int,
        user_id: int,
        period_id: int | None = None,
        employee_id: int | None = None,
    ) -> list[TimeReportOut]:
        return TimekeepingRepository.list_time_reports(
            tenant_id, period_id=period_id, employee_id=employee_id
        )

    @any_employee
    @staticmethod
    def submit_time_report(
        tenant_id: int, report_id: int, user_id: int
    ) -> TimeReportOut:
        report = TimekeepingRepository.get_time_report_by_id(report_id)
        if not report or report.tenant_id != tenant_id:
            raise NotFound(f"Time report {report_id} not found.")
        if report.status != TimeReportStatus.DRAFT:
            raise Conflict(f"Cannot submit report in status '{report.status}'.")
        entries = TimekeepingRepository.list_time_entries(report_id)
        if not entries:
            raise UnprocessableEntity("Cannot submit an empty report.")
        result = TimekeepingRepository.update_time_report_status(
            report_id,
            new_status=TimeReportStatus.SUBMITTED,
            updated_by_id=user_id,
            submitted_at=timezone.now(),
        )
        if user_id is not None:
            TimekeepingRepository.create_status_history(
                report_id,
                from_status=report.status,
                to_status=TimeReportStatus.SUBMITTED,
                changed_by_id=user_id,
            )
        return result

    @only_manager
    @staticmethod
    def approve_time_report(
        tenant_id: int, report_id: int, user_id: int
    ) -> TimeReportOut:
        report = TimekeepingRepository.get_time_report_by_id(report_id)
        if not report or report.tenant_id != tenant_id:
            raise NotFound(f"Time report {report_id} not found.")
        if report.status not in (
            TimeReportStatus.SUBMITTED,
            TimeReportStatus.UNDER_REVIEW,
        ):
            raise Conflict(f"Cannot approve report in status '{report.status}'.")
        result = TimekeepingRepository.update_time_report_status(
            report_id,
            new_status=TimeReportStatus.APPROVED,
            updated_by_id=user_id,
            approved_at=timezone.now(),
        )
        TimekeepingRepository.create_status_history(
            report_id,
            from_status=report.status,
            to_status=TimeReportStatus.APPROVED,
            changed_by_id=user_id,
        )
        return result

    @only_manager
    @staticmethod
    def reject_time_report(
        tenant_id: int,
        report_id: int,
        payload: RejectReportRequest,
        user_id: int,
    ) -> TimeReportOut:
        report = TimekeepingRepository.get_time_report_by_id(report_id)
        if not report or report.tenant_id != tenant_id:
            raise NotFound(f"Time report {report_id} not found.")
        if report.status not in (
            TimeReportStatus.SUBMITTED,
            TimeReportStatus.UNDER_REVIEW,
        ):
            raise Conflict(f"Cannot reject report in status '{report.status}'.")
        result = TimekeepingRepository.update_time_report_status(
            report_id,
            new_status=TimeReportStatus.REJECTED,
            updated_by_id=user_id,
            rejection_reason=payload.reason,
            rejected_at=timezone.now(),
        )
        TimekeepingRepository.create_status_history(
            report_id,
            from_status=report.status,
            to_status=TimeReportStatus.REJECTED,
            changed_by_id=user_id,
            reason=payload.reason,
        )
        return result

    @any_employee
    @staticmethod
    def list_report_history(
        tenant_id: int, report_id: int, user_id: int
    ) -> list[TimeReportStatusHistoryOut]:
        report = TimekeepingRepository.get_time_report_by_id(report_id)
        if not report or report.tenant_id != tenant_id:
            raise NotFound(f"Time report {report_id} not found.")
        return TimekeepingRepository.list_status_history(report_id)

    @any_employee
    @staticmethod
    def create_time_entry(
        tenant_id: int,
        report_id: int,
        payload: TimeEntryIn,
        user_id: int,
    ) -> TimeEntryOut:
        report = TimekeepingRepository.get_time_report_by_id(report_id)
        if not report or report.tenant_id != tenant_id:
            raise NotFound(f"Time report {report_id} not found.")
        if report.status != TimeReportStatus.DRAFT:
            raise UnprocessableEntity(
                f"Cannot add entries to report in status '{report.status}'."
            )
        entity = TimeEntryEntity(
            date=payload.date,
            hours=payload.hours,
            start_time=payload.start_time,
            end_time=payload.end_time,
            description=payload.description,
        )
        return TimekeepingRepository.create_time_entry(
            report_id, entity, created_by_id=user_id
        )

    @any_employee
    @staticmethod
    def list_time_entries(
        tenant_id: int, report_id: int, user_id: int
    ) -> list[TimeEntryOut]:
        report = TimekeepingRepository.get_time_report_by_id(report_id)
        if not report or report.tenant_id != tenant_id:
            raise NotFound(f"Time report {report_id} not found.")
        return TimekeepingRepository.list_time_entries(report_id)

    @any_employee
    @staticmethod
    def update_time_entry(
        tenant_id: int,
        report_id: int,
        entry_id: int,
        payload: TimeEntryUpdate,
        user_id: int,
    ) -> TimeEntryOut:
        report = TimekeepingRepository.get_time_report_by_id(report_id)
        if not report or report.tenant_id != tenant_id:
            raise NotFound(f"Time report {report_id} not found.")
        if report.status != TimeReportStatus.DRAFT:
            raise UnprocessableEntity(
                f"Cannot edit entries in report with status '{report.status}'."
            )
        entry = TimekeepingRepository.get_time_entry_by_id(entry_id)
        if not entry or entry.report_id != report_id:
            raise NotFound(f"Time entry {entry_id} not found.")
        new_entity = TimeEntryEntity(
            date=payload.date,
            hours=payload.hours,
            start_time=payload.start_time,
            end_time=payload.end_time,
            description=payload.description,
        )
        if user_id is not None:
            for field_name, old_val, new_val in [
                ("date", str(entry.date), str(new_entity.date)),
                ("hours", str(entry.hours), str(new_entity.hours)),
                (
                    "start_time",
                    str(entry.start_time) if entry.start_time else None,
                    str(new_entity.start_time) if new_entity.start_time else None,
                ),
                (
                    "end_time",
                    str(entry.end_time) if entry.end_time else None,
                    str(new_entity.end_time) if new_entity.end_time else None,
                ),
                ("description", entry.description, new_entity.description),
            ]:
                if old_val != new_val:
                    TimekeepingRepository.create_entry_change_history(
                        entry_id, field_name, old_val, new_val, user_id
                    )
        return TimekeepingRepository.update_time_entry(
            entry_id, new_entity, updated_by_id=user_id
        )

    @any_employee
    @staticmethod
    def delete_time_entry(
        tenant_id: int,
        report_id: int,
        entry_id: int,
        user_id: int,
    ) -> None:
        report = TimekeepingRepository.get_time_report_by_id(report_id)
        if not report or report.tenant_id != tenant_id:
            raise NotFound(f"Time report {report_id} not found.")
        if report.status != TimeReportStatus.DRAFT:
            raise UnprocessableEntity(
                f"Cannot delete entries in report with status '{report.status}'."
            )
        entry = TimekeepingRepository.get_time_entry_by_id(entry_id)
        if not entry or entry.report_id != report_id:
            raise NotFound(f"Time entry {entry_id} not found.")
        TimekeepingRepository.delete_time_entry(entry_id)
