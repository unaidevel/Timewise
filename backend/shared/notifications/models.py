from django.db import models


class Notification(models.Model):
    class Meta:
        db_table = "notifications_Notification"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
