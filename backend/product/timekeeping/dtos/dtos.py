from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PeriodIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date


class PeriodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    name: str
    start_date: date
    end_date: date
    status: str
    locked_at: datetime | None
    locked_by_id: int | None
    created_by_id: int | None
    updated_by_id: int | None
    created_at: datetime
    updated_at: datetime


class TimeReportIn(BaseModel):
    employee_id: int


class TimeReportOut(TimeReportIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    period_id: int
    status: str
    version: int
    rejection_reason: str
    submitted_at: datetime | None
    approved_at: datetime | None
    rejected_at: datetime | None
    locked_at: datetime | None
    created_by_id: int | None
    updated_by_id: int | None
    created_at: datetime
    updated_at: datetime


class RejectReportRequest(BaseModel):
    reason: str = ""


class TimeEntryIn(BaseModel):
    date: date
    hours: Decimal
    start_time: time | None = None
    end_time: time | None = None
    description: str = ""


class TimeEntryUpdate(BaseModel):
    date_: date | None = None
    hours: Decimal
    start_time: time | None = None
    end_time: time | None = None
    description: str = ""


class TimeEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: int
    date: date
    hours: Decimal
    start_time: time | None
    end_time: time | None
    description: str
    created_by_id: int | None
    updated_by_id: int | None
    created_at: datetime
    updated_at: datetime


class TimeReportStatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: int
    from_status: str | None
    to_status: str
    changed_by_id: int
    reason: str
    changed_at: datetime


class TimeEntryChangeHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entry_id: int
    field_name: str
    old_value: str | None
    new_value: str | None
    changed_by_id: int
    changed_at: datetime
