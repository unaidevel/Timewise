from enum import StrEnum


class MembershipRoles(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    FREELANCE = "freelance"


ROLE_CHOICES = [(role.value, role.name.title()) for role in MembershipRoles]
