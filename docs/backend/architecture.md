# Architecture

The backend enforces a strict layered architecture. Each layer may only depend on the one below it.

```
API → Orchestrator (optional) → Service → Repository
```

| Layer | Directory | Responsibility |
|---|---|---|
| API | `*/api/*.py` | HTTP routing, request/response serialization |
| Orchestrator | `*/orchestrators/*.py` | Cross-module coordination (only when needed) |
| Service | `*/services/*.py` | Business logic |
| Repository | `*/repositories/*.py` | Data access only |

!!! warning "Layer boundary enforcement"
    These rules are enforced by `backend/test_architecture.py`. Any import that crosses a boundary upward will fail CI.

## Module structure

Every domain module follows the same internal layout:

```
product/timekeeping/
├── api/
│   └── router.py
├── services/
│   └── timekeeping_service.py
├── repositories/
│   └── timekeeping_repository.py
├── orchestrators/       # only if cross-module calls are needed
│   └── timekeeping_orchestrator.py
├── models.py
└── dtos.py
```

## DTO conventions

DTOs follow the `In / Out / Update` naming pattern:

- `TimeIn` — creation payload
- `TimeOut` — response shape
- `TimeUpdate` — partial update payload

DTOs use `from_attributes=True` for ORM output. Entities validate all input at construction time.

## Key design decisions

**Orchestrator exists only when needed.** If a service method calls into another module's service, that logic moves to an orchestrator. A service never imports another service.

**Repositories return raw data.** No mapping logic in the repository layer — that lives in the service or entity.

**Entities validate input.** Business invariants (e.g. end time after start time) are enforced in the entity, not in the API or service.
