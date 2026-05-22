from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo


class MembershipRoles(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    FREELANCE = "freelance"


ROLE_CHOICES = [(role.value, role.name.title()) for role in MembershipRoles]


COMMON_TIMEZONES: tuple[str, ...] = (
    "Pacific/Midway",
    "Pacific/Honolulu",
    "America/Anchorage",
    "America/Los_Angeles",
    "America/Denver",
    "America/Chicago",
    "America/New_York",
    "America/Halifax",
    "America/Sao_Paulo",
    "Atlantic/Azores",
    "UTC",
    "Europe/London",
    "Europe/Madrid",
    "Europe/Athens",
    "Europe/Moscow",
    "Asia/Dubai",
    "Asia/Karachi",
    "Asia/Kolkata",
    "Asia/Dhaka",
    "Asia/Bangkok",
    "Asia/Shanghai",
    "Asia/Tokyo",
    "Australia/Sydney",
    "Pacific/Auckland",
)

ALLOWED_TIMEZONES: frozenset[str] = frozenset(COMMON_TIMEZONES)


def _offset_label(tz_name: str) -> str:
    offset = datetime.now(ZoneInfo(tz_name)).utcoffset()
    if offset is None:
        return "UTC+00:00"
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    hours, minutes = divmod(abs(total_minutes), 60)
    return f"UTC{sign}{hours:02d}:{minutes:02d}"


def timezone_choices() -> list[dict[str, str]]:
    return [
        {"value": tz, "label": f"({_offset_label(tz)}) {tz.replace('_', ' ')}"}
        for tz in COMMON_TIMEZONES
    ]
