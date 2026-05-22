from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import OrganizationProfileModel, TenantMembershipModel, TenantModel


@admin.register(TenantModel)
class TenantAdmin(ModelAdmin):
    list_display = ("id", "name", "slug", "is_active", "created_at")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)


@admin.register(TenantMembershipModel)
class TenantMembershipAdmin(ModelAdmin):
    list_display = ("id", "tenant", "user", "role", "joined_at", "left_at")
    search_fields = ("tenant__slug", "user__email")
    list_filter = ("role", "left_at", "tenant")
    list_select_related = ("tenant", "user")


@admin.register(OrganizationProfileModel)
class OrganizationProfileAdmin(ModelAdmin):
    list_display = ("id", "tenant", "public_name", "country", "currency")
    search_fields = ("tenant__slug", "public_name", "legal_name", "vat_number")
    list_filter = ("country", "currency", "tenant")
    list_select_related = ("tenant",)
