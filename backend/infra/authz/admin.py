from django.contrib import admin

from .models import AuthTokenModel, AuthUserModel


@admin.register(AuthUserModel)
class AuthUserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "is_active", "created_at")
    search_fields = ("email", "full_name")
    list_filter = ("is_active",)


@admin.register(AuthTokenModel)
class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "expires_at", "revoked_at")
    search_fields = ("user__email", "token_hash")
    list_filter = ("created_at", "expires_at", "revoked_at")
