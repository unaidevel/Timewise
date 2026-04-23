from enum import Enum


class MembershipRoles(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    FREELANCE = "freelance"


ROLE_CHOICES = [(role.value, role.name.title()) for role in MembershipRoles]
