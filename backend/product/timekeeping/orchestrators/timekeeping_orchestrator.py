from django.db import transaction

from infra.tenants.decorators import any_employee, only_admin, only_manager
from product.timekeeping.dtos.dtos import (
    PeriodIn,
    PeriodOut,
    RejectReportRequest,
    TimeEntryIn,
    TimeEntryOut,
    TimeEntryUpdate,
    TimeReportIn,
    TimeReportOut,
)
from product.timekeeping.services.timekeeping_service import TimekeepingService
from shared.audit.dtos.dtos import AuditEventIn
from shared.audit.services.audit_service import AuditService


class TimekeepingOrchestrator:
    @only_admin
    @staticmethod
    def create_period(
        tenant_id: int,
        payload: PeriodIn,
        user_id: int,
    ) -> PeriodOut:
        with transaction.atomic():
            period = TimekeepingService.create_period(tenant_id, payload, user_id)
            AuditService.create(
                tenant_id,
                AuditEventIn(
                    action="period.created",
                    resource_type="Period",
                    resource_id=period.id,
                    metadata={
                        "name": period.name,
                        "start_date": str(period.start_date),
                        "end_date": str(period.end_date),
                    },
                ),
                user_id,
            )
            return period

    @only_admin
    @staticmethod
    def lock_period(tenant_id: int, period_id: int, user_id: int) -> PeriodOut:
        with transaction.atomic():
            period = TimekeepingService.lock_period(tenant_id, period_id, user_id)
            AuditService.create(
                tenant_id,
                AuditEventIn(
                    action="period.locked",
                    resource_type="Period",
                    resource_id=period.id,
                ),
                user_id,
            )
            return period

    @any_employee
    @staticmethod
    def create_time_report(
        tenant_id: int,
        period_id: int,
        payload: TimeReportIn,
        user_id: int,
    ) -> TimeReportOut:
        with transaction.atomic():
            report = TimekeepingService.create_time_report(
                tenant_id, period_id, payload, user_id
            )
            AuditService.create(
                tenant_id,
                AuditEventIn(
                    action="time_report.created",
                    resource_type="TimeReport",
                    resource_id=report.id,
                    metadata={
                        "period_id": period_id,
                        "employee_id": payload.employee_id,
                    },
                ),
                user_id,
            )
            return report

    @any_employee
    @staticmethod
    def submit_time_report(
        tenant_id: int, report_id: int, user_id: int
    ) -> TimeReportOut:
        previous_status = TimekeepingService.get_report_status(
            tenant_id, report_id, user_id
        )
        with transaction.atomic():
            report = TimekeepingService.submit_time_report(
                tenant_id, report_id, user_id
            )
            AuditService.create(
                tenant_id,
                AuditEventIn(
                    action="time_report.submitted",
                    resource_type="TimeReport",
                    resource_id=report.id,
                    metadata={
                        "from_status": str(previous_status),
                        "to_status": report.status,
                    },
                ),
                user_id,
            )
            return report

    @only_manager
    @staticmethod
    def approve_time_report(
        tenant_id: int, report_id: int, user_id: int
    ) -> TimeReportOut:
        previous_status = TimekeepingService.get_report_status(
            tenant_id, report_id, user_id
        )
        with transaction.atomic():
            report = TimekeepingService.approve_time_report(
                tenant_id, report_id, user_id
            )
            AuditService.create(
                tenant_id,
                AuditEventIn(
                    action="time_report.approved",
                    resource_type="TimeReport",
                    resource_id=report.id,
                    metadata={
                        "from_status": str(previous_status),
                        "to_status": report.status,
                    },
                ),
                user_id,
            )
            return report

    @only_manager
    @staticmethod
    def reject_time_report(
        tenant_id: int,
        report_id: int,
        payload: RejectReportRequest,
        user_id: int,
    ) -> TimeReportOut:
        previous_status = TimekeepingService.get_report_status(
            tenant_id, report_id, user_id
        )
        with transaction.atomic():
            report = TimekeepingService.reject_time_report(
                tenant_id, report_id, payload, user_id
            )
            AuditService.create(
                tenant_id,
                AuditEventIn(
                    action="time_report.rejected",
                    resource_type="TimeReport",
                    resource_id=report.id,
                    metadata={
                        "from_status": str(previous_status),
                        "to_status": report.status,
                        "reason": payload.reason,
                    },
                ),
                user_id,
            )
            return report

    @any_employee
    @staticmethod
    def create_time_entry(
        tenant_id: int,
        report_id: int,
        payload: TimeEntryIn,
        user_id: int,
    ) -> TimeEntryOut:
        with transaction.atomic():
            entry = TimekeepingService.create_time_entry(
                tenant_id, report_id, payload, user_id
            )
            AuditService.create(
                tenant_id,
                AuditEventIn(
                    action="time_entry.created",
                    resource_type="TimeEntry",
                    resource_id=entry.id,
                    metadata={
                        "report_id": report_id,
                        "date": str(entry.date),
                        "hours": str(entry.hours),
                    },
                ),
                user_id,
            )
            return entry

    @any_employee
    @staticmethod
    def update_time_entry(
        tenant_id: int,
        report_id: int,
        entry_id: int,
        payload: TimeEntryUpdate,
        user_id: int,
    ) -> TimeEntryOut:
        with transaction.atomic():
            entry = TimekeepingService.update_time_entry(
                tenant_id, report_id, entry_id, payload, user_id
            )
            AuditService.create(
                tenant_id,
                AuditEventIn(
                    action="time_entry.updated",
                    resource_type="TimeEntry",
                    resource_id=entry.id,
                    metadata={
                        "report_id": report_id,
                        "date": str(entry.date),
                        "hours": str(entry.hours),
                    },
                ),
                user_id,
            )
            return entry

    @any_employee
    @staticmethod
    def delete_time_entry(
        tenant_id: int,
        report_id: int,
        entry_id: int,
        user_id: int,
    ) -> None:
        with transaction.atomic():
            TimekeepingService.delete_time_entry(
                tenant_id, report_id, entry_id, user_id
            )
            AuditService.create(
                tenant_id,
                AuditEventIn(
                    action="time_entry.deleted",
                    resource_type="TimeEntry",
                    resource_id=entry_id,
                    metadata={"report_id": report_id},
                ),
                user_id,
            )
