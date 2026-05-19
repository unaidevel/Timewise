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
from product.timekeeping.entities.timekeeping_entities import (
    PeriodEntity,
    RejectReportEntity,
    TimeEntryEntity,
    TimeEntryUpdateEntity,
    TimeReportEntity,
)
from product.timekeeping.services.timekeeping_service import TimekeepingService
from shared.audit.dtos.dtos import AuditEventIn
from shared.audit.services.audit_service import AuditService
from shared.audit.utils import AUDITED_FAILURES, AuditOutcome, record_failure


class TimekeepingOrchestrator:
    @only_admin
    @staticmethod
    def create_period(
        tenant_id: int,
        payload: PeriodIn,
        user_id: int,
    ) -> PeriodOut:
        entity = PeriodEntity(**payload.model_dump())
        try:
            with transaction.atomic():
                period = TimekeepingService.create_period(tenant_id, entity, user_id)
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="period.created",
                        resource_type="Period",
                        outcome=AuditOutcome.SUCCESS.value,
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
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="period.created",
                resource_type="Period",
                resource_id=None,
                metadata={
                    "name": entity.name,
                    "start_date": str(entity.start_date),
                    "end_date": str(entity.end_date),
                },
                exc=exc,
            )
            raise

    @only_admin
    @staticmethod
    def lock_period(tenant_id: int, period_id: int, user_id: int) -> PeriodOut:
        try:
            with transaction.atomic():
                period = TimekeepingService.lock_period(tenant_id, period_id, user_id)
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="period.locked",
                        resource_type="Period",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=period.id,
                    ),
                    user_id,
                )
                return period
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="period.locked",
                resource_type="Period",
                resource_id=period_id,
                metadata={},
                exc=exc,
            )
            raise

    @any_employee
    @staticmethod
    def create_time_report(
        tenant_id: int,
        period_id: int,
        payload: TimeReportIn,
        user_id: int,
    ) -> TimeReportOut:
        entity = TimeReportEntity(**payload.model_dump())
        try:
            with transaction.atomic():
                report = TimekeepingService.create_time_report(
                    tenant_id, period_id, entity, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="time_report.created",
                        resource_type="TimeReport",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=report.id,
                        metadata={
                            "period_id": period_id,
                            "employee_id": entity.employee_id,
                        },
                    ),
                    user_id,
                )
                return report
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="time_report.created",
                resource_type="TimeReport",
                resource_id=None,
                metadata={
                    "period_id": period_id,
                    "employee_id": entity.employee_id,
                },
                exc=exc,
            )
            raise

    @any_employee
    @staticmethod
    def submit_time_report(
        tenant_id: int, report_id: int, user_id: int
    ) -> TimeReportOut:
        try:
            with transaction.atomic():
                report = TimekeepingService.submit_time_report(
                    tenant_id, report_id, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="time_report.submitted",
                        resource_type="TimeReport",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=report.id,
                        metadata={"to_status": report.status},
                    ),
                    user_id,
                )
                return report
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="time_report.submitted",
                resource_type="TimeReport",
                resource_id=report_id,
                metadata={},
                exc=exc,
            )
            raise

    @only_manager
    @staticmethod
    def approve_time_report(
        tenant_id: int, report_id: int, user_id: int
    ) -> TimeReportOut:
        try:
            with transaction.atomic():
                report = TimekeepingService.approve_time_report(
                    tenant_id, report_id, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="time_report.approved",
                        resource_type="TimeReport",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=report.id,
                        metadata={"to_status": report.status},
                    ),
                    user_id,
                )
                return report
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="time_report.approved",
                resource_type="TimeReport",
                resource_id=report_id,
                metadata={},
                exc=exc,
            )
            raise

    @only_manager
    @staticmethod
    def reject_time_report(
        tenant_id: int,
        report_id: int,
        payload: RejectReportRequest,
        user_id: int,
    ) -> TimeReportOut:
        entity = RejectReportEntity(**payload.model_dump())
        try:
            with transaction.atomic():
                report = TimekeepingService.reject_time_report(
                    tenant_id, report_id, entity, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="time_report.rejected",
                        resource_type="TimeReport",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=report.id,
                        metadata={
                            "to_status": report.status,
                            "reason": entity.reason,
                        },
                    ),
                    user_id,
                )
                return report
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="time_report.rejected",
                resource_type="TimeReport",
                resource_id=report_id,
                metadata={"reason": entity.reason},
                exc=exc,
            )
            raise

    @any_employee
    @staticmethod
    def reopen_time_report(
        tenant_id: int, report_id: int, user_id: int
    ) -> TimeReportOut:
        try:
            with transaction.atomic():
                report = TimekeepingService.reopen_time_report(
                    tenant_id, report_id, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="time_report.reopened",
                        resource_type="TimeReport",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=report.id,
                        metadata={"to_status": report.status},
                    ),
                    user_id,
                )
                return report
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="time_report.reopened",
                resource_type="TimeReport",
                resource_id=report_id,
                metadata={},
                exc=exc,
            )
            raise

    @any_employee
    @staticmethod
    def create_time_entry(
        tenant_id: int,
        report_id: int,
        payload: TimeEntryIn,
        user_id: int,
    ) -> TimeEntryOut:
        entity = TimeEntryEntity(**payload.model_dump())
        try:
            with transaction.atomic():
                created = TimekeepingService.create_time_entry(
                    tenant_id, report_id, entity, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="time_entry.created",
                        resource_type="TimeEntry",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=created.id,
                        metadata={
                            "report_id": report_id,
                            "date": str(created.date),
                            "hours": str(created.hours),
                        },
                    ),
                    user_id,
                )
                return created
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="time_entry.created",
                resource_type="TimeEntry",
                resource_id=None,
                metadata={
                    "report_id": report_id,
                    "date": str(entity.date),
                    "hours": str(entity.hours),
                },
                exc=exc,
            )
            raise

    @any_employee
    @staticmethod
    def update_time_entry(
        tenant_id: int,
        report_id: int,
        entry_id: int,
        payload: TimeEntryUpdate,
        user_id: int,
    ) -> TimeEntryOut:
        entity = TimeEntryUpdateEntity(entry_id=entry_id, **payload.model_dump())
        try:
            with transaction.atomic():
                updated = TimekeepingService.update_time_entry(
                    tenant_id, report_id, entity, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="time_entry.updated",
                        resource_type="TimeEntry",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=updated.id,
                        metadata={
                            "report_id": report_id,
                            "date": str(updated.date),
                            "hours": str(updated.hours),
                        },
                    ),
                    user_id,
                )
                return updated
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="time_entry.updated",
                resource_type="TimeEntry",
                resource_id=entry_id,
                metadata={
                    "report_id": report_id,
                    "date": str(entity.date),
                    "hours": str(entity.hours),
                },
                exc=exc,
            )
            raise

    @any_employee
    @staticmethod
    def delete_time_entry(
        tenant_id: int,
        report_id: int,
        entry_id: int,
        user_id: int,
    ) -> None:
        try:
            with transaction.atomic():
                TimekeepingService.delete_time_entry(
                    tenant_id, report_id, entry_id, user_id
                )
                AuditService.create(
                    tenant_id,
                    AuditEventIn(
                        action="time_entry.deleted",
                        resource_type="TimeEntry",
                        outcome=AuditOutcome.SUCCESS.value,
                        resource_id=entry_id,
                        metadata={"report_id": report_id},
                    ),
                    user_id,
                )
        except AUDITED_FAILURES as exc:
            record_failure(
                tenant_id,
                user_id,
                action="time_entry.deleted",
                resource_type="TimeEntry",
                resource_id=entry_id,
                metadata={"report_id": report_id},
                exc=exc,
            )
            raise
