# Tenants (`infra/tenants`)

Multi-tenant isolation and role-based membership.

## Responsibilities

- Tenant creation and management
- User membership per tenant
- Role assignment (e.g. admin, manager, employee)
- Middleware that injects the current tenant into every request context

## Key design decisions

Tenant isolation is enforced at the repository layer — every query is scoped to the current tenant ID. There is no shared data between tenants.

Roles are per-tenant: a user can be an admin in one tenant and a regular employee in another.
