from enum import StrEnum

from django.db import models


class WorkforceRoles(StrEnum):
    MANAGER = "manager"
    EMPLOYEE = "employee"
    INTERN = "intern"
    FREELANCE = "freelance"
    CUSTOM = "custom"


WORKFORCE_ROLE_CHOICES = [(role.value, role.name.title()) for role in WorkforceRoles]


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


class ApprovalStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class ApprovalAction(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class OvertimeConditionType(models.TextChoices):
    HOURS_EXCEEDED = "hours_exceeded", "Hours Exceeded"
    WEEKLY_HOURS_EXCEEDED = "weekly_hours_exceeded", "Weekly Hours Exceeded"
    DAY_OF_WEEK = "day_of_week", "Day of Week"
    TIME_RANGE = "time_range", "Time Range"
    IS_HOLIDAY = "is_holiday", "Is Holiday"
