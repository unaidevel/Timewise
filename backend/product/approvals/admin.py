from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import TimeReportApprovalEventModel, TimeReportApprovalModel


@admin.register(TimeReportApprovalModel)
class TimeReportApprovalAdmin(ModelAdmin):
    list_display = ("id", "tenant", "report", "status", "reviewer", "reviewed_at")
    search_fields = ("report__employee__full_name", "tenant__slug")
    list_filter = ("status", "tenant")
    list_select_related = ("tenant", "report", "reviewer")


@admin.register(TimeReportApprovalEventModel)
class TimeReportApprovalEventAdmin(ModelAdmin):
    list_display = ("id", "approval", "tenant", "action", "actor", "actioned_at")
    search_fields = (
        "approval__report__employee__full_name",
        "actor__email",
        "approval__tenant__slug",
    )
    list_filter = ("action", "approval__tenant")
    list_select_related = ("approval__tenant", "actor")

    @admin.display(description="Tenant", ordering="approval__tenant__slug")
    def tenant(self, obj):
        return obj.approval.tenant
