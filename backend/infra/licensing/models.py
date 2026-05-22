from django.db import models


class LicensisngModel(models.Model):
    class Meta:
        db_table = "licensing_Licensisng"
        verbose_name = "Licensing"
        verbose_name_plural = "Licensing"
