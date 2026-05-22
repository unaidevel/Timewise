from django.apps import AppConfig


class DemoDataConfig(AppConfig):
    name = "product.demo_data"
    label = "demo_data"
    verbose_name = "Demo data"
    default = True
