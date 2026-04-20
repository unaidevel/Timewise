from enum import Enum


class MembershipRoles(str, Enum):
    OWNER = "owner"
    CREATOR = "creator"
    ADMIN = "admin"
    MEMBER = "member"


ROLE_CHOICES = [(role.value, role.name.title()) for role in MembershipRoles]
