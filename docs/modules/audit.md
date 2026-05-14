# Audit (`shared/audit`)

Append-only log of meaningful actions across the platform.

## Responsibilities

- Record domain actions (`action`, `resource_type`, `resource_id`, `outcome`) with the actor and tenant
- Carry arbitrary structured context via `metadata` and free-form `notes`
- Expose tenant-scoped read endpoints with filters (action, resource, actor, outcome)
- Allow admins to amend `notes` or delete an event when strictly necessary

## Key design decisions

The event payload is treated as immutable apart from the `notes` field — `AuditEventUpdateEntity` only accepts `event_id` and `notes`. Action, resource, outcome and metadata cannot be edited after the fact.

All reads are scoped by `tenant_id` at the repository layer. The service additionally verifies tenant ownership before returning a single event so cross-tenant lookups fail with `NotFound`.

Create and read are available to any authenticated employee; update and delete are gated to tenant admins via decorators.
