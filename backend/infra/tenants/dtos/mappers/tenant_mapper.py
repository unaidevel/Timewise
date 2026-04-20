from infra.tenants.dtos.dtos import TenantMemberResponse, TenantOut
from infra.tenants.dtos.tenant_dtos import Tenant, TenantMembership


def to_tenant(model) -> Tenant:
    return Tenant(
        id=model.id,
        name=model.name,
        slug=model.slug,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
        created_by_id=model.created_by_id,
    )


def to_tenant_membership(model) -> TenantMembership:
    return TenantMembership(
        id=model.id,
        tenant_id=model.tenant_id,
        user_id=model.user_id,
        role=model.role,
        joined_at=model.joined_at,
        invited_by_id=model.invited_by_id,
        left_at=model.left_at,
        left_reason=model.left_reason or None,
    )


def to_tenant_response(tenant: Tenant) -> TenantOut:
    return TenantOut(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


def to_tenant_member_response(membership: TenantMembership) -> TenantMemberResponse:
    return TenantMemberResponse(
        id=membership.id,
        tenant_id=membership.tenant_id,
        user_id=membership.user_id,
        role=membership.role,
        joined_at=membership.joined_at,
        invited_by_id=membership.invited_by_id,
        left_at=membership.left_at,
        left_reason=membership.left_reason,
    )
