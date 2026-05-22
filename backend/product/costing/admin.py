from django.contrib import admin
from unfold.admin import ModelAdmin

from product.costing.models import (
    CostCalculationModel,
    OvertimeRuleModel,
    RuleConditionModel,
)


@admin.register(OvertimeRuleModel)
class OvertimeRuleAdmin(ModelAdmin):
    list_display = (
        "id",
        "name",
        "tenant",
        "multiplier",
        "priority",
        "is_active",
        "created_at",
    )
    search_fields = ("name", "tenant__slug")
    list_filter = ("is_active", "tenant")
    list_select_related = ("tenant",)


@admin.register(RuleConditionModel)
class RuleConditionAdmin(ModelAdmin):
    list_display = ("id", "rule", "tenant", "condition_type", "value", "created_at")
    search_fields = ("rule__name", "rule__tenant__slug")
    list_filter = ("condition_type", "rule__tenant")
    list_select_related = ("rule__tenant",)

    @admin.display(description="Tenant", ordering="rule__tenant__slug")
    def tenant(self, obj):
        return obj.rule.tenant


@admin.register(CostCalculationModel)
class CostCalculationAdmin(ModelAdmin):
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
    list_filter = ("multiplier", "tenant")
    list_select_related = ("tenant", "employee", "time_report")
