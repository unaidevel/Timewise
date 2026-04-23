from django.db import models


class AuditModel(models.Model):
    class Meta:
        db_table = "audit_Audit"
