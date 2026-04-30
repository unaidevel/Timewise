from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class AuthUserModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200)
    password_hash = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "authz_AuthUser"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["is_active"]),
        ]
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="authz_users_email_ci_unique",
            )
        ]

    def __str__(self) -> str:
        return self.email


class AuthTokenModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        AuthUserModel,
        on_delete=models.CASCADE,
        related_name="tokens",
    )
    family_id = models.CharField(max_length=64, db_index=True)
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    refresh_token_hash = models.CharField(max_length=64, unique=True)
    refresh_expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    client_ip = models.CharField(max_length=64, blank=True, default="")
    user_agent = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "authz_AuthToken"
        indexes = [
            models.Index(fields=["expires_at"]),
            models.Index(fields=["refresh_expires_at"]),
            models.Index(fields=["revoked_at"]),
            models.Index(fields=["user", "revoked_at"]),
        ]

    @property
    def is_valid(self) -> bool:
        return self.revoked_at is None and self.expires_at > timezone.now()


class AuthLoginAttemptModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.CharField(max_length=254)
    ip_address = models.CharField(max_length=64)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "authz_AuthLoginAttempt"
        indexes = [
            models.Index(fields=["email", "attempted_at"]),
            models.Index(fields=["ip_address", "attempted_at"]),
        ]


class AuthLoginEventModel(models.Model):
    EVENT_LOGIN_SUCCESS = "login_success"
    EVENT_LOGIN_FAILURE = "login_failure"
    EVENT_LOGOUT = "logout"
    EVENT_REFRESH = "refresh"
    EVENT_REFRESH_REUSE = "refresh_reuse"
    EVENT_RATE_LIMITED = "rate_limited"

    EVENT_CHOICES = [
        (EVENT_LOGIN_SUCCESS, "Login success"),
        (EVENT_LOGIN_FAILURE, "Login failure"),
        (EVENT_LOGOUT, "Logout"),
        (EVENT_REFRESH, "Refresh"),
        (EVENT_REFRESH_REUSE, "Refresh token reuse detected"),
        (EVENT_RATE_LIMITED, "Rate limited"),
    ]

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        related_name="login_events",
        null=True,
        blank=True,
    )
    email = models.CharField(max_length=254, blank=True, default="")
    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
    client_ip = models.CharField(max_length=64, blank=True, default="")
    user_agent = models.CharField(max_length=255, blank=True, default="")
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "authz_AuthLoginEvent"
        indexes = [
            models.Index(fields=["user", "occurred_at"]),
            models.Index(fields=["email", "occurred_at"]),
            models.Index(fields=["event_type", "occurred_at"]),
        ]
