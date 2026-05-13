from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RuleConditionIn(BaseModel):
    condition_type: str = Field(min_length=1)
    value: str = Field(min_length=1, max_length=100)


class RuleConditionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    condition_type: str
    value: str


class OvertimeRuleIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    multiplier: Decimal = Field(ge=Decimal("1.0"))
    priority: int = Field(ge=0)
    conditions: list[RuleConditionIn] = Field(min_length=1)


class OvertimeRuleUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    multiplier: Decimal = Field(ge=Decimal("1.0"))
    priority: int = Field(ge=0)
    conditions: list[RuleConditionIn] = Field(min_length=1)


class OvertimeRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    name: str
    multiplier: Decimal
    priority: int
    is_active: bool
    conditions: list[RuleConditionOut]
    created_by_id: int | None
    updated_by_id: int | None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _materialize_conditions(cls, data: Any) -> Any:
        if hasattr(data, "conditions"):
            manager = data.conditions
            if hasattr(manager, "all"):
                data.__dict__["conditions"] = list(manager.all())
        return data


class HourCostBreakdownOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    time_entry_id: int
    applied_rule_name: str
    multiplier: Decimal
    base_hours: Decimal
    overtime_hours: Decimal
    base_cost: Decimal
    total_cost: Decimal


class ReportCostSummaryOut(BaseModel):
    time_report_id: int
    employee_id: int
    total_base_hours: Decimal
    total_overtime_hours: Decimal
    total_base_cost: Decimal
    total_cost: Decimal
    breakdowns: list[HourCostBreakdownOut]
