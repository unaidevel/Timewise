from django.contrib import admin
from unfold.admin import ModelAdmin

from product.timekeeping.models import PeriodModel, TimeEntryModel, TimeReportModel


@admin.register(PeriodModel)
class PeriodAdmin(ModelAdmin):
    list_display = (
        "id",
        "name",
        "tenant",
        "status",
        "start_date",
        "end_date",
        "locked_at",
    )
    search_fields = ("name", "tenant__slug")
    list_filter = ("status", "tenant")
    list_select_related = ("tenant",)


@admin.register(TimeReportModel)
class TimeReportAdmin(ModelAdmin):
    list_display = ("id", "tenant", "employee", "period", "status", "submitted_at")
    search_fields = ("employee__full_name", "tenant__slug", "period__name")
    list_filter = ("status", "tenant")
    list_select_related = ("tenant", "employee", "period")


@admin.register(TimeEntryModel)
class TimeEntryAdmin(ModelAdmin):
    list_display = ("id", "tenant", "report", "date", "hours", "start_time", "end_time")
    search_fields = ("report__employee__full_name", "report__tenant__slug")
    list_filter = ("date", "report__tenant")
    list_select_related = ("report__tenant",)

    @admin.display(description="Tenant", ordering="report__tenant__slug")
    def tenant(self, obj):
        return obj.report.tenant
