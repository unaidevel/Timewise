from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal

from infra.common.http_exceptions import UnprocessableEntity


@dataclass(frozen=True, slots=True)
class PeriodEntity:
    name: str
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", self._validate_name(self.name))
        self._validate_dates(self.start_date, self.end_date)

    @staticmethod
    def _validate_name(value: str) -> str:
        clean = value.strip()
        if not clean:
            raise UnprocessableEntity("Period name cannot be blank.")
        if len(clean) > 100:
            raise UnprocessableEntity("Period name cannot exceed 100 characters.")
        return clean

    @staticmethod
    def _validate_dates(start_date: date, end_date: date) -> None:
        if end_date <= start_date:
            raise UnprocessableEntity(
                f"End date ({end_date}) must be after start date ({start_date})."
            )


@dataclass(frozen=True, slots=True)
class TimeEntryEntity:
    date: date
    hours: Decimal
    start_time: time | None = None
    end_time: time | None = None
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "hours", self._validate_hours(self.hours))
        if self.start_time is not None and self.end_time is not None:
            self._validate_time_range(self.start_time, self.end_time)

    @staticmethod
    def _validate_hours(value: Decimal) -> Decimal:
        if value <= Decimal("0"):
            raise UnprocessableEntity("Hours must be greater than zero.")
        if value > Decimal("24"):
            raise UnprocessableEntity("Hours cannot exceed 24 per day.")
        if abs(value.as_tuple().exponent) > 2:
            raise UnprocessableEntity("Hours cannot have more than 2 decimal places.")
        return value

    @staticmethod
    def _validate_time_range(start_time: time, end_time: time) -> None:
        if end_time <= start_time:
            raise UnprocessableEntity(
                f"End time ({end_time}) must be after start time ({start_time})."
            )
