from django.contrib import admin

from .models import AuditEventModel


@admin.register(AuditEventModel)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "actor",
        "action",
        "resource_type",
        "resource_id",
        "occurred_at",
    )
    list_filter = ("action", "resource_type")
    search_fields = ("action", "resource_type", "notes")
    readonly_fields = ("occurred_at",)
