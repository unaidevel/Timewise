from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = "shared.common"
    label = "common"
    verbose_name = "Common"
    default = True
