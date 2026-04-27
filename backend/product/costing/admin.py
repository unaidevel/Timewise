from django.contrib import admin

from product.costing.models import (
    CostCalculationModel,
    OvertimeRuleModel,
    RuleConditionModel,
)


@admin.register(OvertimeRuleModel)
class OvertimeRuleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "tenant",
        "multiplier",
        "priority",
        "is_active",
        "created_at",
    )
    search_fields = ("name", "tenant__slug")
    list_filter = ("is_active",)


@admin.register(RuleConditionModel)
class RuleConditionAdmin(admin.ModelAdmin):
    list_display = ("rule", "condition_type", "value", "created_at")
    search_fields = ("rule__name",)
    list_filter = ("condition_type",)


@admin.register(CostCalculationModel)
class CostCalculationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "time_report",
        "employee",
        "applied_rule_name",
        "multiplier",
        "total_cost",
        "calculated_at",
    )
    search_fields = ("employee__full_name", "applied_rule_name", "tenant__slug")
    list_filter = ("multiplier",)
