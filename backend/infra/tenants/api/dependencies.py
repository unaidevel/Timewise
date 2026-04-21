from typing import Annotated

from fastapi import Depends, HTTPException, status

from infra.authz.api.dependencies import CurrentUser
from infra.authz.dtos.auth_dtos import AuthUser
from infra.common.classes import MembershipRoles
from infra.tenants.models import TenantMembershipModel


def require_role(*roles: MembershipRoles) -> type:
    def _check(tenant_id: int, user: CurrentUser) -> AuthUser:
        membership = TenantMembershipModel.objects.filter(
            tenant_id=tenant_id,
            user_id=user.id,
            left_at__isnull=True,
        ).first()
        if not membership or membership.role not in {r.value for r in roles}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this tenant.",
            )
        return user

    return Annotated[AuthUser, Depends(_check)]
