<div class="hero">
  <div class="hero__title">TimeWise</div>
  <div class="hero__subtitle">
    Employee time tracking and labour cost management platform — built to showcase production-grade backend engineering.
  </div>
  <div class="hero__buttons">
    <a class="hero__btn hero__btn--primary" href="backend/">Backend docs</a>
    <a class="hero__btn hero__btn--secondary" href="https://github.com/unaidevel/Timewise">GitHub</a>
  </div>
</div>

<div class="features">
  <div class="feature-card">
    <div class="feature-card__icon">🏗️</div>
    <div class="feature-card__title">Hexagonal architecture</div>
    <div class="feature-card__desc">Strict layer separation enforced by architecture tests in CI. Domain logic never touches the framework.</div>
  </div>
  <div class="feature-card">
    <div class="feature-card__icon">⚙️</div>
    <div class="feature-card__title">Cost-rule engine</div>
    <div class="feature-card__desc">Data-driven rules for overtime, holidays, and contract types. New policies added without changing code.</div>
  </div>
  <div class="feature-card">
    <div class="feature-card__icon">✅</div>
    <div class="feature-card__title">Approval workflow</div>
    <div class="feature-card__desc">Multi-step approvals with immutable status history. Every transition is auditable.</div>
  </div>
  <div class="feature-card">
    <div class="feature-card__icon">🔒</div>
    <div class="feature-card__title">Multi-tenant</div>
    <div class="feature-card__desc">Full tenant isolation at the repository layer. Role-based access control per tenant.</div>
  </div>
</div>

## Stack

=== "Backend"

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

=== "Frontend"

    | Layer | Technology |
    |---|---|
    | Framework | React 19 + TypeScript 6 |
    | Bundler | Vite 8 |
    | Routing | React Router 7 |
    | Server state | TanStack Query v5 |
    | UI components | shadcn/ui + Radix primitives |
    | Styling | Tailwind CSS v4 |
    | API client | @hey-api/openapi-ts (auto-generated) |
    | Testing | Vitest + Testing Library + MSW |

## Modules

| Module | Status | Description |
|---|---|---|
| `infra/authz` | ✅ Done | JWT authentication, login attempts, account lockout |
| `infra/tenants` | ✅ Done | Multi-tenant isolation, role-based membership |
| `product/workforce` | ✅ Done | Employees, contracts, and organisational structure |
| `product/timekeeping` | ✅ Done | Time reports, shift entries, overtime detection, approval flow |
| `product/costing` | ✅ Done | Configurable rule engine mapping hours to costs |
| `product/approvals` | ✅ Done | Multi-step approval workflow with full status history |
| `shared/audit` | 🔜 Planned | Domain event sourcing for full audit trail |

## Quick start

```bash
git clone https://github.com/unaidevel/Timewise.git
cd TimeWise
cp backend/.env/.env.example backend/.env/.env
docker compose up --build
```

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Django admin | http://localhost:8000/admin/ |
| Frontend | http://localhost:3000 |
