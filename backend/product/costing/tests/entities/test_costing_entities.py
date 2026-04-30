from decimal import Decimal

import pytest

from infra.common.exceptions import UnprocessableEntity
from product.costing.entities.costing_entities import OvertimeRuleEntity


def test_overtime_rule_entity_accepts_valid_values():
    entity = OvertimeRuleEntity(
        name="Weekend Premium", multiplier=Decimal("1.50"), priority=1
    )

    assert entity.name == "Weekend Premium"
    assert entity.multiplier == Decimal("1.50")
    assert entity.priority == 1


def test_overtime_rule_entity_strips_name():
    entity = OvertimeRuleEntity(
        name="  Holiday Rate  ", multiplier=Decimal("2.00"), priority=0
    )

    assert entity.name == "Holiday Rate"


def test_overtime_rule_entity_rejects_blank_name():
    with pytest.raises(UnprocessableEntity, match="cannot be blank"):
        OvertimeRuleEntity(name="   ", multiplier=Decimal("1.5"), priority=0)


def test_overtime_rule_entity_rejects_empty_name():
    with pytest.raises(UnprocessableEntity, match="cannot be blank"):
        OvertimeRuleEntity(name="", multiplier=Decimal("1.5"), priority=0)


def test_overtime_rule_entity_rejects_name_over_200_chars():
    with pytest.raises(UnprocessableEntity, match="200 characters"):
        OvertimeRuleEntity(name="x" * 201, multiplier=Decimal("1.5"), priority=0)


def test_overtime_rule_entity_accepts_name_at_max_length():
    entity = OvertimeRuleEntity(name="x" * 200, multiplier=Decimal("1.5"), priority=0)

    assert entity.name == "x" * 200


def test_overtime_rule_entity_rejects_multiplier_below_one():
    with pytest.raises(UnprocessableEntity, match=r"at least 1\.0"):
        OvertimeRuleEntity(name="Bad", multiplier=Decimal("0.99"), priority=0)


def test_overtime_rule_entity_accepts_multiplier_exactly_one():
    entity = OvertimeRuleEntity(name="Standard", multiplier=Decimal("1.0"), priority=0)

    assert entity.multiplier == Decimal("1.0")


def test_overtime_rule_entity_rejects_multiplier_with_three_decimal_places():
    with pytest.raises(UnprocessableEntity, match="2 decimal places"):
        OvertimeRuleEntity(name="TooPrecise", multiplier=Decimal("1.555"), priority=0)


def test_overtime_rule_entity_accepts_multiplier_with_two_decimal_places():
    entity = OvertimeRuleEntity(name="OK", multiplier=Decimal("1.55"), priority=0)

    assert entity.multiplier == Decimal("1.55")


def test_overtime_rule_entity_accepts_integer_multiplier():
    entity = OvertimeRuleEntity(name="Double", multiplier=Decimal("2"), priority=0)

    assert entity.multiplier == Decimal("2")


def test_overtime_rule_entity_rejects_negative_priority():
    with pytest.raises(UnprocessableEntity, match="0 or greater"):
        OvertimeRuleEntity(name="Negative", multiplier=Decimal("1.5"), priority=-1)


def test_overtime_rule_entity_accepts_priority_zero():
    entity = OvertimeRuleEntity(name="First", multiplier=Decimal("1.5"), priority=0)

    assert entity.priority == 0


def test_overtime_rule_entity_accepts_large_priority():
    entity = OvertimeRuleEntity(name="Last", multiplier=Decimal("1.5"), priority=999)

    assert entity.priority == 999


def test_overtime_rule_entity_is_frozen():
    entity = OvertimeRuleEntity(name="Locked", multiplier=Decimal("1.5"), priority=0)

    with pytest.raises(AttributeError):
        entity.name = "Modified"
