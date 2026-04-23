import functools
import inspect

from infra.common.classes import MembershipRoles
from infra.common.http_exceptions import Forbidden
from infra.tenants.models import TenantMembershipModel


def require_membership_role(*roles: MembershipRoles):
    """
    Service-layer decorator that enforces tenant membership role.

    The decorated method must expose both ``tenant_id: int`` and
    ``user_id: int`` as named parameters so the decorator can resolve them.

    Supports both ``@require_membership_role(...) @staticmethod`` and
    ``@staticmethod @require_membership_role(...)`` ordering.

    Raises Forbidden if the user is not an active
    member of the tenant with one of the required roles.
    """

    def decorator(func_or_static):
        is_static = isinstance(func_or_static, staticmethod)
        func = func_or_static.__func__ if is_static else func_or_static
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            tenant_id = bound.arguments.get("tenant_id")
            user_id = bound.arguments.get("user_id")

            if tenant_id is not None and user_id is not None:
                membership = TenantMembershipModel.objects.filter(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    left_at__isnull=True,
                ).first()
                if not membership or membership.role not in {r.value for r in roles}:
                    raise Forbidden(
                        "Insufficient permissions for this tenant."
                    )

            return func(*args, **kwargs)

        return staticmethod(wrapper) if is_static else wrapper

    return decorator


only_owner = require_membership_role(MembershipRoles.OWNER)
only_admin = require_membership_role(MembershipRoles.OWNER, MembershipRoles.ADMIN)
only_manager = require_membership_role(MembershipRoles.OWNER, MembershipRoles.ADMIN)
only_member = require_membership_role(
    MembershipRoles.OWNER,
    MembershipRoles.CREATOR,
    MembershipRoles.ADMIN,
    MembershipRoles.MEMBER,
)
