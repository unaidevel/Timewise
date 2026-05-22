from django.db import models

from infra.authz.models import AuthUserModel
from infra.tenants.models import TenantModel
from product.common.classes import OvertimeConditionType
from product.timekeeping.models import TimeEntryModel, TimeReportModel
from product.workforce.models import EmployeeModel


class OvertimeRuleModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        TenantModel,
        on_delete=models.CASCADE,
        related_name="overtime_rules",
    )
    name = models.CharField(max_length=200)
    multiplier = models.DecimalField(max_digits=5, decimal_places=2)
    priority = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_overtime_rules",
    )
    updated_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_overtime_rules",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "costing_OvertimeRule"
        verbose_name = "Overtime rule"
        verbose_name_plural = "Overtime rules"
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["tenant", "priority"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_overtime_rule_name_per_tenant",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} (x{self.multiplier})"


class RuleConditionModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    rule = models.ForeignKey(
        OvertimeRuleModel,
        on_delete=models.CASCADE,
        related_name="conditions",
    )
    condition_type = models.CharField(
        max_length=30,
        choices=OvertimeConditionType.choices,
    )
    value = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "costing_RuleCondition"
        verbose_name = "Rule condition"
        verbose_name_plural = "Rule conditions"
        indexes = [
            models.Index(fields=["rule", "condition_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.condition_type}={self.value}"


class CostCalculationModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        TenantModel,
        on_delete=models.CASCADE,
        related_name="cost_calculations",
    )
    time_report = models.ForeignKey(
        TimeReportModel,
        on_delete=models.PROTECT,
        related_name="cost_calculations",
    )
    time_entry = models.ForeignKey(
        TimeEntryModel,
        on_delete=models.CASCADE,
        related_name="cost_calculation",
    )
    employee = models.ForeignKey(
        EmployeeModel,
        on_delete=models.PROTECT,
        related_name="cost_calculations",
    )
    applied_rule_name = models.CharField(max_length=200, blank=True, default="")
    multiplier = models.DecimalField(max_digits=5, decimal_places=2)
    base_hours = models.DecimalField(max_digits=5, decimal_places=2)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2)
    base_cost = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    calculated_by = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cost_calculations",
    )
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "costing_CostCalculation"
        verbose_name = "Cost calculation"
        verbose_name_plural = "Cost calculations"
        indexes = [
            models.Index(fields=["tenant", "time_report"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["time_entry"],
                name="unique_calculation_per_entry",
            )
        ]

    def __str__(self) -> str:
        return f"Calc {self.id} — entry {self.time_entry_id} (x{self.multiplier})"
