from django.apps import AppConfig


class AuthzConfig(AppConfig):
    name = "infra.authz"
    label = "authz"
    verbose_name = "Authentication"
    default = True
