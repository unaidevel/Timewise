from fastapi import APIRouter, Query, status

from infra.authz.api.dependencies import CurrentUser
from infra.common.exceptions import (
    Conflict,
    Forbidden,
    NotFound,
    UnprocessableEntity,
    responses_for,
)
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
from product.timekeeping.services.timekeeping_service import TimekeepingService

router = APIRouter(prefix="/api/v1/tenants/{tenant_id}", tags=["timekeeping"])


@router.post(
    "/periods",
    response_model=PeriodOut,
    responses=responses_for(Forbidden, Conflict, UnprocessableEntity),
    status_code=status.HTTP_201_CREATED,
)
def create_period(
    tenant_id: int,
    payload: PeriodIn,
    current_user: CurrentUser,
) -> PeriodOut:
    return TimekeepingService.create_period(tenant_id, payload, current_user.id)


@router.get("/periods", response_model=list[PeriodOut])
def list_periods(
    tenant_id: int,
    current_user: CurrentUser,
    status: str | None = Query(default=None),
) -> list[PeriodOut]:
    return TimekeepingService.list_periods(tenant_id, status=status)


@router.get(
    "/periods/{period_id}", response_model=PeriodOut, responses=responses_for(NotFound)
)
def get_period(tenant_id: int, period_id: int, current_user: CurrentUser) -> PeriodOut:
    return TimekeepingService.get_period(tenant_id, period_id)


@router.post(
    "/periods/{period_id}/lock",
    response_model=PeriodOut,
    responses=responses_for(Forbidden, NotFound, Conflict),
)
def lock_period(tenant_id: int, period_id: int, current_user: CurrentUser) -> PeriodOut:
    return TimekeepingService.lock_period(tenant_id, period_id, user_id=current_user.id)


@router.post(
    "/periods/{period_id}/reports",
    response_model=TimeReportOut,
    responses=responses_for(NotFound, Conflict),
    status_code=status.HTTP_201_CREATED,
)
def create_time_report(
    tenant_id: int,
    period_id: int,
    payload: TimeReportIn,
    current_user: CurrentUser,
) -> TimeReportOut:
    return TimekeepingService.create_time_report(
        tenant_id, period_id, payload, user_id=current_user.id
    )


@router.get("/periods/{period_id}/reports", response_model=list[TimeReportOut])
def list_time_reports_for_period(
    tenant_id: int,
    period_id: int,
    _: CurrentUser,
) -> list[TimeReportOut]:
    return TimekeepingService.list_time_reports(tenant_id, period_id=period_id)


@router.get(
    "/reports/{report_id}",
    response_model=TimeReportOut,
    responses=responses_for(NotFound),
)
def get_time_report(tenant_id: int, report_id: int, _: CurrentUser) -> TimeReportOut:
    return TimekeepingService.get_time_report(tenant_id, report_id)


@router.post(
    "/reports/{report_id}/submit",
    response_model=TimeReportOut,
    responses=responses_for(NotFound, Conflict, UnprocessableEntity),
)
def submit_time_report(
    tenant_id: int, report_id: int, current_user: CurrentUser
) -> TimeReportOut:
    return TimekeepingService.submit_time_report(
        tenant_id, report_id, user_id=current_user.id
    )


@router.post(
    "/reports/{report_id}/approve",
    response_model=TimeReportOut,
    responses=responses_for(Forbidden, NotFound, Conflict),
)
def approve_time_report(
    tenant_id: int, report_id: int, current_user: CurrentUser
) -> TimeReportOut:
    return TimekeepingService.approve_time_report(
        tenant_id, report_id, user_id=current_user.id
    )


@router.post(
    "/reports/{report_id}/reject",
    response_model=TimeReportOut,
    responses=responses_for(Forbidden, NotFound, Conflict),
)
def reject_time_report(
    tenant_id: int,
    report_id: int,
    payload: RejectReportRequest,
    current_user: CurrentUser,
) -> TimeReportOut:
    return TimekeepingService.reject_time_report(
        tenant_id, report_id, payload, user_id=current_user.id
    )


@router.get(
    "/reports/{report_id}/history",
    response_model=list[TimeReportStatusHistoryOut],
    responses=responses_for(NotFound),
)
def list_report_history(
    tenant_id: int, report_id: int, _: CurrentUser
) -> list[TimeReportStatusHistoryOut]:
    return TimekeepingService.list_report_history(tenant_id, report_id)


@router.post(
    "/reports/{report_id}/entries",
    response_model=TimeEntryOut,
    responses=responses_for(NotFound, Conflict, UnprocessableEntity),
    status_code=status.HTTP_201_CREATED,
)
def create_time_entry(
    tenant_id: int,
    report_id: int,
    payload: TimeEntryIn,
    current_user: CurrentUser,
) -> TimeEntryOut:
    return TimekeepingService.create_time_entry(
        tenant_id, report_id, payload, current_user.id
    )


@router.get(
    "/reports/{report_id}/entries",
    response_model=list[TimeEntryOut],
    responses=responses_for(NotFound),
)
def list_time_entries(
    tenant_id: int, report_id: int, _: CurrentUser
) -> list[TimeEntryOut]:
    return TimekeepingService.list_time_entries(tenant_id, report_id)


@router.put(
    "/reports/{report_id}/entries/{entry_id}",
    response_model=TimeEntryOut,
    responses=responses_for(NotFound, Conflict, UnprocessableEntity),
)
def update_time_entry(
    tenant_id: int,
    report_id: int,
    entry_id: int,
    payload: TimeEntryUpdate,
    current_user: CurrentUser,
) -> TimeEntryOut:
    return TimekeepingService.update_time_entry(
        tenant_id, report_id, entry_id, payload, user_id=current_user.id
    )


@router.delete(
    "/reports/{report_id}/entries/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=responses_for(NotFound, Conflict),
)
def delete_time_entry(
    tenant_id: int,
    report_id: int,
    entry_id: int,
    current_user: CurrentUser,
) -> None:
    TimekeepingService.delete_time_entry(
        tenant_id, report_id, entry_id, user_id=current_user.id
    )
