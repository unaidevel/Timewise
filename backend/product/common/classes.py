

from django.db import models


class PeriodStatus(models.TextChoices):
    OPEN = "open", "Open"
    LOCKED = "locked", "Locked"

class TimeReportStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    UNDER_REVIEW = "under_review", "Under Review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    LOCKED = "locked", "Locked"

