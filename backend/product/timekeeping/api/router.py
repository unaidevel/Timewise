from fastapi import APIRouter, HTTPException, Query, status

from infra.authz.api.dependencies import CurrentUser
from infra.common.responses import STATUS_RESPONSES
from infra.tenants.exceptions import InsufficientPermissionsError
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
from product.timekeeping.exceptions import (
    InvalidPeriodDatesError,
    InvalidTimeEntryError,
    InvalidTimeReportStatusTransitionError,
    PeriodAlreadyExistsError,
    PeriodAlreadyLockedError,
    PeriodNotFoundError,
    TimeEntryNotFoundError,
    TimeReportAlreadyExistsError,
    TimeReportNotEditableError,
    TimeReportNotFoundError,
)
from product.timekeeping.services.timekeeping_service import TimekeepingService

router = APIRouter(prefix="/api/v1/tenants/{tenant_id}", tags=["timekeeping"])




@router.post(
    "/periods",
    response_model=PeriodOut,
    responses=STATUS_RESPONSES,
    status_code=status.HTTP_201_CREATED,
)
def create_period(
    tenant_id: int,
    payload: PeriodIn,
    current_user: CurrentUser,
) -> PeriodOut:
    try:
        return TimekeepingService.create_period(tenant_id, payload, current_user.id)
    except InsufficientPermissionsError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except PeriodAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidPeriodDatesError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.get("/periods", response_model=list[PeriodOut])
def list_periods(
    tenant_id: int,
    current_user: CurrentUser,
    status: str | None = Query(default=None),
) -> list[PeriodOut]:
    return TimekeepingService.list_periods(tenant_id, status=status)


@router.get("/periods/{period_id}", response_model=PeriodOut)
def get_period(tenant_id: int, period_id: int, current_user: CurrentUser) -> PeriodOut:
    return TimekeepingService.get_period(tenant_id, period_id, current_user.id)


@router.post("/periods/{period_id}/lock", response_model=PeriodOut)
def lock_period(tenant_id: int, period_id: int, current_user: CurrentUser) -> PeriodOut:
    try:
        return TimekeepingService.lock_period(tenant_id, period_id, user_id=current_user.id)
    except InsufficientPermissionsError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except PeriodNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PeriodAlreadyLockedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post(
    "/periods/{period_id}/reports",
    response_model=TimeReportOut,
    responses=STATUS_RESPONSES,
    status_code=status.HTTP_201_CREATED,
)
def create_time_report(
    tenant_id: int,
    period_id: int,
    payload: TimeReportIn,
    current_user: CurrentUser,
) -> TimeReportOut:
    try:
        return TimekeepingService.create_time_report(
            tenant_id, period_id, payload, user_id=current_user.id
        )
    except PeriodNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PeriodAlreadyLockedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except TimeReportAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/periods/{period_id}/reports", response_model=list[TimeReportOut])
def list_time_reports_for_period(
    tenant_id: int,
    period_id: int,
    _: CurrentUser,
) -> list[TimeReportOut]:
    return TimekeepingService.list_time_reports(tenant_id, period_id=period_id)


@router.get("/reports/{report_id}", response_model=TimeReportOut)
def get_time_report(tenant_id: int, report_id: int, _: CurrentUser) -> TimeReportOut:
    try:
        return TimekeepingService.get_time_report(tenant_id, report_id)
    except TimeReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/reports/{report_id}/submit", response_model=TimeReportOut)
def submit_time_report(
    tenant_id: int, report_id: int, current_user: CurrentUser
) -> TimeReportOut:
    try:
        return TimekeepingService.submit_time_report(
            tenant_id, report_id, user_id=current_user.id
        )
    except TimeReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidTimeReportStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except TimeReportNotEditableError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.post("/reports/{report_id}/approve", response_model=TimeReportOut)
def approve_time_report(
    tenant_id: int, report_id: int, current_user: CurrentUser
) -> TimeReportOut:
    try:
        return TimekeepingService.approve_time_report(
            tenant_id, report_id, user_id=current_user.id
        )
    except InsufficientPermissionsError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TimeReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidTimeReportStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/reports/{report_id}/reject", response_model=TimeReportOut)
def reject_time_report(
    tenant_id: int,
    report_id: int,
    payload: RejectReportRequest,
    current_user: CurrentUser,
) -> TimeReportOut:
    try:
        return TimekeepingService.reject_time_report(
            tenant_id, report_id, payload, user_id=current_user.id
        )
    except InsufficientPermissionsError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TimeReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidTimeReportStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/reports/{report_id}/history", response_model=list[TimeReportStatusHistoryOut])
def list_report_history(
    tenant_id: int, report_id: int, current_user: CurrentUser
) -> list[TimeReportStatusHistoryOut]:
    try:
        return TimekeepingService.list_report_history(tenant_id, report_id, current_user.id)
    except TimeReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc



@router.post(
    "/reports/{report_id}/entries",
    response_model=TimeEntryOut,
    responses=STATUS_RESPONSES,
    status_code=status.HTTP_201_CREATED,
)
def create_time_entry(
    tenant_id: int,
    report_id: int,
    payload: TimeEntryIn,
    current_user: CurrentUser,
) -> TimeEntryOut:
    try:
        return TimekeepingService.create_time_entry(
            tenant_id, report_id, payload, current_user.id
        )
    except TimeReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TimeReportNotEditableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidTimeEntryError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.get("/reports/{report_id}/entries", response_model=list[TimeEntryOut])
def list_time_entries(
    tenant_id: int, report_id: int, _: CurrentUser
) -> list[TimeEntryOut]:
    try:
        return TimekeepingService.list_time_entries(tenant_id, report_id)
    except TimeReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/reports/{report_id}/entries/{entry_id}", response_model=TimeEntryOut)
def update_time_entry(
    tenant_id: int,
    report_id: int,
    entry_id: int,
    payload: TimeEntryUpdate,
    current_user: CurrentUser,
) -> TimeEntryOut:
    try:
        return TimekeepingService.update_time_entry(
            tenant_id, report_id, entry_id, payload, user_id=current_user.id
        )
    except TimeReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TimeReportNotEditableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except TimeEntryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidTimeEntryError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.delete(
    "/reports/{report_id}/entries/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_time_entry(
    tenant_id: int,
    report_id: int,
    entry_id: int,
    current_user: CurrentUser,
) -> None:
    try:
        TimekeepingService.delete_time_entry(
            tenant_id, report_id, entry_id, user_id=current_user.id
        )
    except TimeReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TimeReportNotEditableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except TimeEntryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
