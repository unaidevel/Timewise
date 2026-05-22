from django.apps import AppConfig


class TenantsConfig(AppConfig):
    name = "infra.tenants"
    label = "tenants"
    verbose_name = "Tenants"
    default = True
