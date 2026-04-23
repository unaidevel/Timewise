from django.db import models


class SharedModel(models.Model):
    class Meta:
        db_table = "common_Shared"
