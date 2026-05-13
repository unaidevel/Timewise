from django.utils import timezone

from infra.common.exceptions import Conflict, NotFound, UnprocessableEntity
from infra.tenants.decorators import any_employee, only_admin, only_manager
from product.common.classes import PeriodStatus, TimeReportStatus
from product.timekeeping.dtos.dtos import (
    PeriodOut,
    TimeEntryOut,
    TimeReportOut,
    TimeReportStatusHistoryOut,
)
from product.timekeeping.entities.timekeeping_entities import (
    PeriodEntity,
    RejectReportEntity,
    TimeEntryEntity,
    TimeEntryUpdateEntity,
    TimeReportEntity,
)
from product.timekeeping.repositories.timekeeping_repository import (
    TimekeepingRepository,
)


class TimekeepingService:
    @only_admin
    @staticmethod
    def create_period(
        tenant_id: int,
        entity: PeriodEntity,
        user_id: int,
    ) -> PeriodOut:
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
        entity: TimeReportEntity,
        user_id: int,
    ) -> TimeReportOut:
        period = TimekeepingRepository.get_period_by_id(period_id)
        if not period or period.tenant_id != tenant_id:
            raise NotFound(f"Period {period_id} not found.")
        if period.status == PeriodStatus.LOCKED:
            raise Conflict(f"Period {period_id} is locked. Cannot create reports.")
        existing = TimekeepingRepository.find_report_by_employee_and_period(
            entity.employee_id, period_id
        )
        if existing:
            raise Conflict(
                f"Employee {entity.employee_id} already has a report for period {period_id}."
            )
        return TimekeepingRepository.create_time_report(
            employee_id=entity.employee_id,
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
    def get_report_status(
        tenant_id: int, report_id: int, user_id: int
    ) -> TimeReportStatus:
        status = TimekeepingRepository.get_report_status(report_id)
        if not status:
            raise NotFound(f"Time report {report_id} not found.")
        return status

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
        result = TimekeepingRepository.submit_time_report(
            report_id,
            updated_by_id=user_id,
            submitted_at=timezone.now(),
        )
        if result is None:
            raise NotFound(f"Time report {report_id} not found.")
        TimekeepingRepository.create_status_history(
            report_id,
            from_status=report.status,
            to_status=str(TimeReportStatus.SUBMITTED),
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
        result = TimekeepingRepository.approve_time_report(
            report_id,
            updated_by_id=user_id,
            approved_at=timezone.now(),
        )
        if result is None:
            raise NotFound(f"Time report {report_id} not found.")
        TimekeepingRepository.create_status_history(
            report_id,
            from_status=report.status,
            to_status=str(TimeReportStatus.APPROVED),
            changed_by_id=user_id,
        )
        return result

    @only_manager
    @staticmethod
    def reject_time_report(
        tenant_id: int,
        report_id: int,
        entity: RejectReportEntity,
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
        result = TimekeepingRepository.reject_time_report(
            report_id,
            updated_by_id=user_id,
            rejection_reason=entity.reason,
            rejected_at=timezone.now(),
        )
        if result is None:
            raise NotFound(f"Time report {report_id} not found.")
        TimekeepingRepository.create_status_history(
            report_id,
            from_status=report.status,
            to_status=str(TimeReportStatus.REJECTED),
            changed_by_id=user_id,
            reason=entity.reason,
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
        entity: TimeEntryEntity,
        user_id: int,
    ) -> TimeEntryOut:
        report = TimekeepingRepository.get_time_report_by_id(report_id)
        if not report or report.tenant_id != tenant_id:
            raise NotFound(f"Time report {report_id} not found.")
        if report.status != TimeReportStatus.DRAFT:
            raise UnprocessableEntity(
                f"Cannot add entries to report in status '{report.status}'."
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
        entity: TimeEntryUpdateEntity,
        user_id: int,
    ) -> TimeEntryOut:
        report = TimekeepingRepository.get_time_report_by_id(report_id)
        if not report or report.tenant_id != tenant_id:
            raise NotFound(f"Time report {report_id} not found.")
        if report.status != TimeReportStatus.DRAFT:
            raise UnprocessableEntity(
                f"Cannot edit entries in report with status '{report.status}'."
            )
        entry = TimekeepingRepository.get_time_entry_by_id(entity.entry_id)
        if not entry or entry.report_id != report_id:
            raise NotFound(f"Time entry {entity.entry_id} not found.")
        for field_name, old_val, new_val in [
            ("date", str(entry.date), str(entity.date)),
            ("hours", str(entry.hours), str(entity.hours)),
            (
                "start_time",
                str(entry.start_time) if entry.start_time else None,
                str(entity.start_time) if entity.start_time else None,
            ),
            (
                "end_time",
                str(entry.end_time) if entry.end_time else None,
                str(entity.end_time) if entity.end_time else None,
            ),
            ("description", entry.description, entity.description),
        ]:
            if old_val != new_val:
                TimekeepingRepository.create_entry_change_history(
                    entity.entry_id, field_name, old_val, new_val, user_id
                )
        return TimekeepingRepository.update_time_entry(entity, updated_by_id=user_id)

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
