from django.apps import AppConfig


class AuditConfig(AppConfig):
    name = "shared.audit"
    label = "audit"
    verbose_name = "Audit"
    default = True
