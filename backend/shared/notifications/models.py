from django.db import models


class Notification(models.Model):
    class Meta:
        db_table = "notifications_Notification"
