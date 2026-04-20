from django.contrib import admin

from .models import TenantMembershipModel, TenantModel


@admin.register(TenantModel)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)


@admin.register(TenantMembershipModel)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ("tenant", "user", "role", "joined_at", "left_at")
    search_fields = ("tenant__slug", "user__email")
    list_filter = ("role", "left_at")
