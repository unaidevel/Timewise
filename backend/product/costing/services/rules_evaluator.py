"""
Pure overtime rules evaluator — no database, no external imports.
All logic is deterministic and fully unit-testable without Django setup.
"""

from dataclasses import dataclass, field
from datetime import date, time
from decimal import Decimal

HOURS_EXCEEDED = "hours_exceeded"
WEEKLY_HOURS_EXCEEDED = "weekly_hours_exceeded"
DAY_OF_WEEK = "day_of_week"
TIME_RANGE = "time_range"
IS_HOLIDAY = "is_holiday"


@dataclass
class EntryContext:
    entry_id: int
    date: date
    hours: Decimal
    start_time: time | None
    end_time: time | None
    weekly_hours_so_far: Decimal


@dataclass
class ConditionSpec:
    condition_type: str
    value: str


@dataclass
class RuleSpec:
    name: str
    multiplier: Decimal
    priority: int
    conditions: list[ConditionSpec] = field(default_factory=list)


@dataclass
class HourCostBreakdown:
    entry_id: int
    applied_rule_name: str
    multiplier: Decimal
    base_hours: Decimal
    overtime_hours: Decimal
    base_cost: Decimal
    total_cost: Decimal


class RulesEvaluator:
    """
    Evaluates which overtime rule applies to a time entry and calculates cost.

    Rules are sorted by priority descending — highest priority wins.
    All conditions on a rule must match (implicit AND).
    If no rule matches, base rate applies (multiplier = 1.0).
    """

    def evaluate(
        self,
        entry: EntryContext,
        hourly_rate: Decimal,
        rules: list[RuleSpec],
        holidays: set[date],
    ) -> HourCostBreakdown:
        sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            if self._rule_matches(rule, entry, holidays):
                return self._calculate(entry, hourly_rate, rule.name, rule.multiplier)

        return self._calculate(entry, hourly_rate, "", Decimal("1.00"))

    def _rule_matches(
        self,
        rule: RuleSpec,
        entry: EntryContext,
        holidays: set[date],
    ) -> bool:
        return all(
            self._condition_matches(cond, entry, holidays) for cond in rule.conditions
        )

    def _condition_matches(
        self,
        condition: ConditionSpec,
        entry: EntryContext,
        holidays: set[date],
    ) -> bool:
        match condition.condition_type:
            case _ if condition.condition_type == HOURS_EXCEEDED:
                return entry.hours > Decimal(condition.value)

            case _ if condition.condition_type == WEEKLY_HOURS_EXCEEDED:
                return entry.weekly_hours_so_far > Decimal(condition.value)

            case _ if condition.condition_type == DAY_OF_WEEK:
                allowed = {int(d) for d in condition.value.split(",")}
                return entry.date.isoweekday() in allowed

            case _ if condition.condition_type == TIME_RANGE:
                if entry.start_time is None or entry.end_time is None:
                    return False
                start_str, end_str = condition.value.split("-")
                range_start = time.fromisoformat(start_str.strip())
                range_end = time.fromisoformat(end_str.strip())
                if range_start <= range_end:
                    # Normal range (e.g. 09:00-17:00)
                    return entry.start_time < range_end and entry.end_time > range_start
                else:
                    # Crossing midnight (e.g. 22:00-06:00)
                    return entry.end_time > range_start or entry.start_time < range_end

            case _ if condition.condition_type == IS_HOLIDAY:
                return entry.date in holidays

        return False

    def _calculate(
        self,
        entry: EntryContext,
        hourly_rate: Decimal,
        rule_name: str,
        multiplier: Decimal,
    ) -> HourCostBreakdown:
        base_cost = entry.hours * hourly_rate
        total_cost = base_cost * multiplier
        overtime_hours = entry.hours if rule_name else Decimal("0.00")
        return HourCostBreakdown(
            entry_id=entry.entry_id,
            applied_rule_name=rule_name,
            multiplier=multiplier,
            base_hours=entry.hours,
            overtime_hours=overtime_hours,
            base_cost=base_cost.quantize(Decimal("0.01")),
            total_cost=total_cost.quantize(Decimal("0.01")),
        )
