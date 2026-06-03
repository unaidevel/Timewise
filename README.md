# TimeWise

Employee time tracking and labour cost management platform built as a portfolio project to showcase production-grade backend engineering.

## What it does

TimeWise lets companies track employee working hours, apply configurable cost rules, and generate cost reports — with a full approval workflow and a complete audit trail.



## Technical highlights

- **Strict layered architecture** inspired by clean/hexagonal principles — framework-independent domain entities and one-way layer dependencies (API → Orchestrator → Service → Repository), enforced by architecture tests in CI
- **FastAPI** as the HTTP layer with **Django ORM** for models and migrations
- **Domain entities** with business rules enforced independently of the framework
- **Configurable cost-rule engine** for overtime, holidays, and contract types
- **Multi-step approval workflow** with status history and role-based access control
- Full **CI pipeline** with linting, static type checking, architecture validation, and PostgreSQL-backed integration tests
- **Pre-commit hooks** enforcing Ruff and conventional commit messages locally (via [czg](https://github.com/Zhengqbbb/cz-git))
- **Docker Compose** setup for local development

## Stack

**Backend**

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

**Frontend**

| Layer | Technology |
|---|---|
| Framework | React 19 + TypeScript 6 |
| Bundler | Vite 8 |
| Routing | React Router 7 |
| Server state | TanStack Query v5 |
| UI components | shadcn/ui + Radix primitives |
| Styling | Tailwind CSS v4 |
| API client | @hey-api/openapi-ts (auto-generated from FastAPI schema) |
| Linting / formatting | Biome |
| Testing | Vitest + Testing Library + MSW |

## Modules

| Module | Status | Description |
|---|---|---|
| `infra/authz` | Done | JWT authentication, login attempts, account lockout |
| `infra/tenants` | Done | Multi-tenant isolation, role-based membership |
| `product/workforce` | Done | Employees, contracts, and organisational structure |
| `product/timekeeping` | Done | Time reports, shift entries, overtime detection, approval flow |
| `product/costing` | Done | Configurable rule engine mapping hours to costs |
| `product/approvals` | Done | Multi-step approval workflow with full status history |
| `shared/audit` | Done | Append-only audit log with admin-only update/delete |
| `infra/licensing` | WIP / internal | Tenant licensing and entitlements |
| `shared/notifications` | WIP / internal | Notification delivery |
| `product/demo_data` | WIP / internal | Demo data seeding for showcase environments |

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

**3. Open the app**

The dev compose runs `migrate` and `collectstatic` automatically on startup, so no separate migration step is needed.

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Django admin | http://localhost:8000/admin/ |
| Frontend | http://localhost:3000 |

---

## Deploy to a VPS

Production runs the same images behind [Caddy](https://caddyserver.com/), which
terminates TLS, serves the static frontend and proxies `/api`, `/admin`, `/static`
and the docs to the backend. Neither the backend (8000) nor Postgres (5432) is
exposed to the host.

**1. Point DNS and open ports**

Add an `A` record for your subdomain (e.g. `timewise.unaimunoz.dev`) pointing at
the VPS IP, and open ports `80` and `443` — Caddy needs them for the Let's Encrypt
challenge. Set the domain in [`Caddyfile`](Caddyfile) if you use a different one.

**2. Configure environment**

```bash
git clone https://github.com/unaidevel/Timewise.git
cd TimeWise

cp .env.example .env                                   # Postgres credentials for the db container
cp backend/.env/prod.env.example backend/.env/prod.env # backend production config

# Generate a secret key:
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Fill in `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, the `CORS_ALLOWED_ORIGINS` /
`DJANGO_CSRF_TRUSTED_ORIGINS` origins and a strong `POSTGRES_PASSWORD`. The
`POSTGRES_*` values in `.env` and `backend/.env/prod.env` must match.

> `VITE_API_URL` is empty in production so the frontend calls the API same-origin
> (`/api/v1/...`). It is inlined at build time — changing the domain requires
> rebuilding the frontend image.

**3. Start the stack**

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Passing explicit `-f` files skips the dev override, so `--reload` and bind mounts
are not used. The backend runs `migrate` and `collectstatic` on startup.

**4. Create an admin user**

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  exec backend uv run python manage.py createsuperuser
```

The app is then served at `https://<your-domain>/`, with the Django admin at
`/admin/` and the API docs at `/docs`.

### Redeploying (CI/CD)

The [`VPS Deploy`](.github/workflows/vps-deploy.yml) workflow updates the running
stack on demand. Trigger it manually from the repo's **Actions → VPS Deploy → Run
workflow**. It SSHes into the VPS, pulls `main` and runs `up -d --build`, so the
backend and frontend images are rebuilt with the new code (the database and Caddy
are left untouched).

It needs these repository secrets (**Settings → Secrets and variables → Actions**):

| Secret | Value |
|---|---|
| `VPS_HOST` | VPS IP or hostname |
| `VPS_USER` | SSH user on the VPS (use a non-root, deploy-only user) |
| `VPS_SSH_KEY` | Private SSH key whose public half is in the VPS `authorized_keys` |
| `VPS_PROJECT_PATH` | Absolute path to the cloned repo on the VPS |

The same thing can be run by hand on the VPS with `make prod`.

---

Without Docker, see [Backend](backend/README.md) and [Frontend](frontend/README.md) for local setup.