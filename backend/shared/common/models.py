from django.db import models


class SharedModel(models.Model):
    class Meta:
        db_table = "common_Shared"
        verbose_name = "Shared"
        verbose_name_plural = "Shared"
