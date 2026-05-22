from django.contrib import admin

from .models import OrganizationProfileModel, TenantMembershipModel, TenantModel


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


@admin.register(OrganizationProfileModel)
class OrganizationProfileAdmin(admin.ModelAdmin):
    list_display = ("tenant", "public_name", "country", "currency")
    search_fields = ("tenant__slug", "public_name", "legal_name", "vat_number")
    list_filter = ("country", "currency")
