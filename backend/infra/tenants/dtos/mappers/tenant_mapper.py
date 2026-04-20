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
