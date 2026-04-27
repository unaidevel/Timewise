from datetime import date, time
from decimal import Decimal

import pytest

from infra.common.exceptions import UnprocessableEntity
from product.timekeeping.entities.timekeeping_entities import (
    PeriodEntity,
    TimeEntryEntity,
)


class TestPeriodEntity:
    def test_strips_whitespace_from_name(self):
        entity = PeriodEntity(
            name="  Q1 2025  ", start_date=date(2025, 1, 1), end_date=date(2025, 3, 31)
        )
        assert entity.name == "Q1 2025"

    def test_raises_on_blank_name(self):
        with pytest.raises(UnprocessableEntity, match="cannot be blank"):
            PeriodEntity(
                name="   ", start_date=date(2025, 1, 1), end_date=date(2025, 3, 31)
            )

    def test_raises_on_name_exceeding_100_chars(self):
        with pytest.raises(UnprocessableEntity, match="100 characters"):
            PeriodEntity(
                name="x" * 101, start_date=date(2025, 1, 1), end_date=date(2025, 3, 31)
            )

    def test_accepts_name_exactly_100_chars(self):
        entity = PeriodEntity(
            name="x" * 100, start_date=date(2025, 1, 1), end_date=date(2025, 3, 31)
        )
        assert len(entity.name) == 100

    def test_raises_when_end_date_before_start_date(self):
        with pytest.raises(UnprocessableEntity, match="after start date"):
            PeriodEntity(
                name="Q1", start_date=date(2025, 3, 31), end_date=date(2025, 1, 1)
            )

    def test_raises_when_end_date_equals_start_date(self):
        with pytest.raises(UnprocessableEntity, match="after start date"):
            PeriodEntity(
                name="Q1", start_date=date(2025, 1, 1), end_date=date(2025, 1, 1)
            )

    def test_accepts_valid_dates(self):
        entity = PeriodEntity(
            name="Q1", start_date=date(2025, 1, 1), end_date=date(2025, 3, 31)
        )
        assert entity.start_date == date(2025, 1, 1)
        assert entity.end_date == date(2025, 3, 31)


class TestTimeEntryEntity:
    def test_accepts_valid_hours(self):
        entity = TimeEntryEntity(date=date(2025, 1, 15), hours=Decimal("8.00"))
        assert entity.hours == Decimal("8.00")

    def test_raises_on_hours_zero(self):
        with pytest.raises(UnprocessableEntity, match="greater than zero"):
            TimeEntryEntity(date=date(2025, 1, 15), hours=Decimal("0"))

    def test_raises_on_negative_hours(self):
        with pytest.raises(UnprocessableEntity, match="greater than zero"):
            TimeEntryEntity(date=date(2025, 1, 15), hours=Decimal("-1"))

    def test_raises_on_hours_exceeding_24(self):
        with pytest.raises(UnprocessableEntity, match="cannot exceed 24"):
            TimeEntryEntity(date=date(2025, 1, 15), hours=Decimal("24.01"))

    def test_accepts_exactly_24_hours(self):
        entity = TimeEntryEntity(date=date(2025, 1, 15), hours=Decimal("24"))
        assert entity.hours == Decimal("24")

    def test_raises_on_hours_with_more_than_2_decimals(self):
        with pytest.raises(UnprocessableEntity, match="2 decimal places"):
            TimeEntryEntity(date=date(2025, 1, 15), hours=Decimal("7.505"))

    def test_accepts_hours_with_2_decimals(self):
        entity = TimeEntryEntity(date=date(2025, 1, 15), hours=Decimal("7.50"))
        assert entity.hours == Decimal("7.50")

    def test_raises_when_end_time_before_start_time(self):
        with pytest.raises(UnprocessableEntity, match="after start time"):
            TimeEntryEntity(
                date=date(2025, 1, 15),
                hours=Decimal("8"),
                start_time=time(17, 0),
                end_time=time(9, 0),
            )

    def test_raises_when_end_time_equals_start_time(self):
        with pytest.raises(UnprocessableEntity, match="after start time"):
            TimeEntryEntity(
                date=date(2025, 1, 15),
                hours=Decimal("8"),
                start_time=time(9, 0),
                end_time=time(9, 0),
            )

    def test_accepts_valid_time_range(self):
        entity = TimeEntryEntity(
            date=date(2025, 1, 15),
            hours=Decimal("8"),
            start_time=time(9, 0),
            end_time=time(17, 0),
        )
        assert entity.start_time == time(9, 0)
        assert entity.end_time == time(17, 0)

    def test_accepts_only_start_time_without_end_time(self):
        entity = TimeEntryEntity(
            date=date(2025, 1, 15),
            hours=Decimal("8"),
            start_time=time(9, 0),
        )
        assert entity.start_time == time(9, 0)
        assert entity.end_time is None
