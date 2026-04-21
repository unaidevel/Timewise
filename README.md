# TimeWise

Employee time tracking and labour cost management platform built as a portfolio project to showcase production-grade backend engineering.

## What it does

TimeWise lets companies track employee working hours, apply configurable cost rules, and generate cost reports — with a full approval workflow and a complete audit trail.

## Technical highlights

- **Hexagonal architecture** (ports & adapters) strictly separating domain, application, and infrastructure layers
- **FastAPI** as the HTTP layer with **Django ORM** for models and migrations
- **Domain entities** with business rules enforced independently of the framework
- **Configurable cost-rule engine** for overtime, holidays, and contract types (planned)
- **Optimistic locking** on approval workflows to handle concurrent state transitions (planned)
- **Domain events** for audit logging (planned)
- Full **CI pipeline** with linting, type checking, and PostgreSQL-backed integration tests
- **Docker Compose** setup for local development

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| ORM / Admin | Django |
| Database | PostgreSQL |
| Package manager | uv |
| Testing | pytest |
| Linting | Ruff |
| CI | GitHub Actions |
| Deploy | Railway |

## Modules

| Module | Status | Description |
|---|---|---|
| `infra/authz` | Done | JWT authentication, login attempts, account lockout |
| `infra/tenants` | Done | Multi-tenant isolation |
| `product/workforce` | In progress | Employees, contracts, and organisational structure |
| `product/timekeeping` | Planned | Clock-in/out, shift entries, overtime detection |
| `product/costing` | Planned | Configurable rule engine mapping hours to costs |
| `product/approvals` | Planned | Multi-step approval workflow with optimistic locking |
| `shared/audit` | Planned | Domain event sourcing for full audit trail |

## Project structure

```
backend/
├── api/            # FastAPI app and route registry
├── config/         # Django settings, URLs, management commands
├── infra/          # Infrastructure modules (auth, tenants, licensing)
├── product/        # Business domain modules
└── shared/         # Cross-cutting concerns (audit, base classes)
```

## Documentation

- [Backend setup and commands](backend/README.md)
