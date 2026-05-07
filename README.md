# TimeWise

Employee time tracking and labour cost management platform built as a portfolio project to showcase production-grade backend engineering.

## What it does

TimeWise lets companies track employee working hours, apply configurable cost rules, and generate cost reports — with a full approval workflow and a complete audit trail.



## Technical highlights

- **Hexagonal architecture** (ports & adapters) strictly separating domain, application, and infrastructure layers
- **FastAPI** as the HTTP layer with **Django ORM** for models and migrations
- **Domain entities** with business rules enforced independently of the framework
- **Configurable cost-rule engine** for overtime, holidays, and contract types
- **Multi-step approval workflow** with status history and role-based access control
- Full **CI pipeline** with linting, static type checking, architecture validation, and PostgreSQL-backed integration tests
- **Pre-commit hooks** enforcing Ruff and conventional commit messages locally (via [czg](https://github.com/Zhengqbbb/cz-git))
- **Docker Compose** setup for local development

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| ORM / Admin | Django |
| Database | PostgreSQL |
| Package manager | uv |
| Testing | pytest + pytest-cov |
| Linting | Ruff |
| Type checking | mypy |
| CI | GitHub Actions |
| Deploy | Railway |

## Modules

| Module | Status | Description |
|---|---|---|
| `infra/authz` | Done | JWT authentication, login attempts, account lockout |
| `infra/tenants` | Done | Multi-tenant isolation, role-based membership |
| `product/workforce` | Done | Employees, contracts, and organisational structure |
| `product/timekeeping` | Done | Time reports, shift entries, overtime detection, approval flow |
| `product/costing` | Done | Configurable rule engine mapping hours to costs |
| `product/approvals` | Done | Multi-step approval workflow with full status history |
| `shared/audit` | Planned | Domain event sourcing for full audit trail |

## Project structure

```
backend/
├── api/            # FastAPI app and route registry
├── config/         # Django settings, URLs, management commands
├── infra/          # Infrastructure modules (auth, tenants)
├── product/        # Business domain modules
└── shared/         # Cross-cutting concerns (audit, base classes)
```

## Documentation

- [Backend](backend/README.md)
- [Frontend](frontend/README.md)



## Getting started


**1. Clone and configure**

```bash
git clone https://github.com/unaidevel/Timewise.git
cd TimeWise
cp backend/.env/.env.example backend/.env/.env
# Fill in your PostgreSQL credentials in backend/.env/.env
```

**2. Start the stack**

```bash
docker compose up --build
```

**3. Run migrations**

```bash
docker compose run --rm admin uv run python manage.py migrate
```

**4. Open the app**

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Django admin | http://localhost:8000/admin/ |
| Frontend | http://localhost:3000 |

---

Without Docker, see [Backend](backend/README.md) and [Frontend](frontend/README.md) for local setup.