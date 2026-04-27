"""
Pure unit tests for RulesEvaluator — no database, no Django setup required.
"""

from datetime import date, time
from decimal import Decimal

from django.test import SimpleTestCase

from product.costing.services.rules_evaluator import (
    ConditionSpec,
    EntryContext,
    RuleSpec,
    RulesEvaluator,
)

SATURDAY = date(2025, 1, 4)   # isoweekday() == 6
SUNDAY = date(2025, 1, 5)     # isoweekday() == 7
MONDAY = date(2025, 1, 6)     # isoweekday() == 1
HOLIDAY = date(2025, 12, 25)

RATE = Decimal("20.00")


def make_entry(
    *,
    hours: Decimal = Decimal("8.00"),
    d: date = MONDAY,
    start_time: time | None = None,
    end_time: time | None = None,
    weekly_hours_so_far: Decimal = Decimal("8.00"),
) -> EntryContext:
    return EntryContext(
        entry_id=1,
        date=d,
        hours=hours,
        start_time=start_time,
        end_time=end_time,
        weekly_hours_so_far=weekly_hours_so_far,
    )


def make_rule(
    *,
    condition_type: str,
    value: str,
    multiplier: str = "1.50",
    priority: int = 1,
) -> RuleSpec:
    return RuleSpec(
        name="Test rule",
        multiplier=Decimal(multiplier),
        priority=priority,
        conditions=[ConditionSpec(condition_type=condition_type, value=value)],
    )


class RulesEvaluatorTests(SimpleTestCase):
    def setUp(self):
        self.evaluator = RulesEvaluator()

    # --- DAY_OF_WEEK ---

    def test_weekend_rule_applies_on_saturday(self):
        rule = make_rule(condition_type="day_of_week", value="6,7", multiplier="1.75")
        entry = make_entry(d=SATURDAY)
        result = self.evaluator.evaluate(entry, RATE, [rule], holidays=set())
        assert result.multiplier == Decimal("1.75")
        assert result.applied_rule_name == "Test rule"

    def test_weekend_rule_applies_on_sunday(self):
        rule = make_rule(condition_type="day_of_week", value="6,7")
        entry = make_entry(d=SUNDAY)
        result = self.evaluator.evaluate(entry, RATE, [rule], holidays=set())
        assert result.multiplier == Decimal("1.50")

    def test_weekend_rule_does_not_apply_on_monday(self):
        rule = make_rule(condition_type="day_of_week", value="6,7")
        entry = make_entry(d=MONDAY)
        result = self.evaluator.evaluate(entry, RATE, [rule], holidays=set())
        assert result.multiplier == Decimal("1.00")
        assert result.applied_rule_name == ""

    # --- IS_HOLIDAY ---

    def test_holiday_rule_applies_when_date_in_holidays(self):
        rule = make_rule(condition_type="is_holiday", value="true", multiplier="2.00")
        entry = make_entry(d=HOLIDAY)
        result = self.evaluator.evaluate(entry, RATE, [rule], holidays={HOLIDAY})
        assert result.multiplier == Decimal("2.00")
        assert result.applied_rule_name == "Test rule"

    def test_holiday_rule_does_not_apply_when_date_not_in_holidays(self):
        rule = make_rule(condition_type="is_holiday", value="true", multiplier="2.00")
        entry = make_entry(d=MONDAY)
        result = self.evaluator.evaluate(entry, RATE, [rule], holidays={HOLIDAY})
        assert result.multiplier == Decimal("1.00")

    # --- HOURS_EXCEEDED ---

    def test_hours_exceeded_applies_when_hours_above_threshold(self):
        rule = make_rule(condition_type="hours_exceeded", value="8")
        entry = make_entry(hours=Decimal("9.00"))
        result = self.evaluator.evaluate(entry, RATE, [rule], holidays=set())
        assert result.multiplier == Decimal("1.50")

    def test_hours_exceeded_does_not_apply_when_hours_equal_threshold(self):
        rule = make_rule(condition_type="hours_exceeded", value="8")
        entry = make_entry(hours=Decimal("8.00"))
        result = self.evaluator.evaluate(entry, RATE, [rule], holidays=set())
        assert result.multiplier == Decimal("1.00")

    def test_hours_exceeded_does_not_apply_when_hours_below_threshold(self):
        rule = make_rule(condition_type="hours_exceeded", value="8")
        entry = make_entry(hours=Decimal("7.50"))
        result = self.evaluator.evaluate(entry, RATE, [rule], holidays=set())
        assert result.multiplier == Decimal("1.00")

    # --- WEEKLY_HOURS_EXCEEDED ---

    def test_weekly_hours_exceeded_applies_when_accumulated_above_threshold(self):
        rule = make_rule(condition_type="weekly_hours_exceeded", value="40")
        entry = make_entry(hours=Decimal("8.00"), weekly_hours_so_far=Decimal("42.00"))
        result = self.evaluator.evaluate(entry, RATE, [rule], holidays=set())
        assert result.multiplier == Decimal("1.50")

    def test_weekly_hours_exceeded_does_not_apply_at_threshold(self):
        rule = make_rule(condition_type="weekly_hours_exceeded", value="40")
        entry = make_entry(hours=Decimal("8.00"), weekly_hours_so_far=Decimal("40.00"))
        result = self.evaluator.evaluate(entry, RATE, [rule], holidays=set())
        assert result.multiplier == Decimal("1.00")

    # --- TIME_RANGE ---

    def test_time_range_applies_when_entry_overlaps_range(self):
        rule = make_rule(condition_type="time_range", value="22:00-06:00")
        entry = make_entry(
            start_time=time(21, 0),
            end_time=time(23, 0),
        )
        result = self.evaluator.evaluate(entry, RATE, [rule], holidays=set())
        assert result.multiplier == Decimal("1.50")

    def test_time_range_does_not_apply_when_no_overlap(self):
        rule = make_rule(condition_type="time_range", value="22:00-06:00")
        entry = make_entry(
            start_time=time(9, 0),
            end_time=time(17, 0),
        )
        result = self.evaluator.evaluate(entry, RATE, [rule], holidays=set())
        assert result.multiplier == Decimal("1.00")

    def test_time_range_skips_when_entry_has_no_times(self):
        rule = make_rule(condition_type="time_range", value="22:00-06:00")
        entry = make_entry(start_time=None, end_time=None)
        result = self.evaluator.evaluate(entry, RATE, [rule], holidays=set())
        assert result.multiplier == Decimal("1.00")

    # --- PRIORITY ---

    def test_higher_priority_rule_wins_over_lower(self):
        low = RuleSpec(
            name="Low priority",
            multiplier=Decimal("1.50"),
            priority=1,
            conditions=[ConditionSpec("day_of_week", "6,7")],
        )
        high = RuleSpec(
            name="High priority",
            multiplier=Decimal("2.00"),
            priority=10,
            conditions=[ConditionSpec("day_of_week", "6,7")],
        )
        entry = make_entry(d=SATURDAY)
        result = self.evaluator.evaluate(entry, RATE, [low, high], holidays=set())
        assert result.multiplier == Decimal("2.00")
        assert result.applied_rule_name == "High priority"

    # --- NO RULE ---

    def test_no_rule_returns_base_rate(self):
        entry = make_entry()
        result = self.evaluator.evaluate(entry, RATE, [], holidays=set())
        assert result.multiplier == Decimal("1.00")
        assert result.applied_rule_name == ""
        assert result.base_cost == Decimal("160.00")   # 8h * 20
        assert result.total_cost == Decimal("160.00")
        assert result.overtime_hours == Decimal("0.00")

    # --- MULTIPLE CONDITIONS (AND logic) ---

    def test_all_conditions_must_match(self):
        rule = RuleSpec(
            name="Weekend + overtime",
            multiplier=Decimal("2.00"),
            priority=1,
            conditions=[
                ConditionSpec("day_of_week", "6,7"),
                ConditionSpec("hours_exceeded", "8"),
            ],
        )
        # Saturday but only 7h — both conditions not met
        entry_short = make_entry(d=SATURDAY, hours=Decimal("7.00"))
        result = self.evaluator.evaluate(entry_short, RATE, [rule], holidays=set())
        assert result.multiplier == Decimal("1.00")

        # Saturday with 9h — both conditions met
        entry_long = make_entry(d=SATURDAY, hours=Decimal("9.00"))
        result = self.evaluator.evaluate(entry_long, RATE, [rule], holidays=set())
        assert result.multiplier == Decimal("2.00")

    # --- COST CALCULATION ---

    def test_cost_calculation_is_correct_with_rule(self):
        rule = make_rule(condition_type="day_of_week", value="6,7", multiplier="1.50")
        entry = make_entry(d=SATURDAY, hours=Decimal("8.00"))
        result = self.evaluator.evaluate(entry, RATE, [rule], holidays=set())
        assert result.base_cost == Decimal("160.00")   # 8 * 20
        assert result.total_cost == Decimal("240.00")  # 160 * 1.5
        assert result.base_hours == Decimal("8.00")
        assert result.overtime_hours == Decimal("8.00")
