from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import AuditEventModel


@admin.register(AuditEventModel)
class AuditEventAdmin(ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "actor",
        "action",
        "resource_type",
        "resource_id",
        "occurred_at",
    )
    list_filter = ("action", "resource_type", "tenant")
    search_fields = ("action", "resource_type", "notes", "tenant__slug")
    readonly_fields = ("occurred_at",)
    list_select_related = ("tenant", "actor")
