# Auth (`infra/authz`)

JWT-based authentication with brute-force protection.

## Responsibilities

- Issue and validate JWT access tokens
- Track failed login attempts per user
- Lock accounts after a configurable number of failures
- Expose login, logout, and token-refresh endpoints

## Key design decisions

Account lockout state is stored in the database (not in-memory) so it survives restarts and works across multiple API instances.

Token validation is stateless — no database lookup per request. Revocation is handled at logout by short token TTLs combined with refresh token rotation.
