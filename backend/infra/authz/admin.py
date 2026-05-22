from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    AuthLoginAttemptModel,
    AuthLoginEventModel,
    AuthTokenModel,
    AuthUserModel,
)


@admin.register(AuthUserModel)
class AuthUserAdmin(ModelAdmin):
    list_display = ("id", "email", "full_name", "is_active", "created_at")
    search_fields = ("email", "full_name")
    list_filter = ("is_active",)


@admin.register(AuthTokenModel)
class AuthTokenAdmin(ModelAdmin):
    list_display = (
        "id",
        "user",
        "client_ip",
        "user_agent",
        "created_at",
        "expires_at",
        "revoked_at",
    )
    search_fields = ("user__email", "token_hash", "family_id")
    list_filter = ("created_at", "expires_at", "revoked_at")
    readonly_fields = ("token_hash", "refresh_token_hash", "family_id")


@admin.register(AuthLoginAttemptModel)
class AuthLoginAttemptAdmin(ModelAdmin):
    list_display = ("id", "email", "ip_address", "attempted_at")
    search_fields = ("email", "ip_address")
    list_filter = ("attempted_at",)


@admin.register(AuthLoginEventModel)
class AuthLoginEventAdmin(ModelAdmin):
    list_display = (
        "id",
        "occurred_at",
        "event_type",
        "email",
        "user",
        "client_ip",
    )
    search_fields = ("email", "user__email", "client_ip")
    list_filter = ("event_type", "occurred_at")
    readonly_fields = ("occurred_at",)
