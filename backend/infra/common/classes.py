from enum import Enum


class MembershipRoles(str, Enum):
    OWNER = "owner"
    CREATOR = "creator"
    ADMIN = "admin"
    MEMBER = "member"
