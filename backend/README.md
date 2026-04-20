## Backend

This backend uses:

- `FastAPI` as the HTTP/API framework
- `Django` only for ORM, models, and migrations
- `uv` for dependency management and command execution

## UV-native workflow

Install dependencies:

```powershell
uv sync
```

Run the FastAPI app:

```powershell
uv run uvicorn main:app --reload
```

Run Django management commands:

```powershell
uv run python manage.py check
uv run python manage.py makemigrations
uv run python manage.py migrate
```

Run development tools:

```powershell
uv run pytest
uv run python manage.py test
uv run python manage.py testall
uv run python manage.py testall --coverage
uv run ruff check .
```

`testall` also supports `--keepdb`, `--dropdb`, and `--coverage`.

## Notes

- Prefer `uv run ...` instead of calling `.venv\Scripts\python.exe` directly.
- `manage.py` still works because Django needs settings for ORM and migrations.
- `core/settings.py` is intentionally minimal because FastAPI is the web layer.
- Environment variables are loaded from `backend/.env/global.env`, `backend/.env/auth.env`, `backend/.env/.env`, or `backend/.env/.env.local`.
- Start by copying `backend/.env/.env.example` to `backend/.env/.env` and filling in your PostgreSQL values.
- Test setup uses `POSTGRES_MAINTENANCE_DB` when present; otherwise it reuses `POSTGRES_DB` to create/drop the test database without requiring a separate `postgres` database.
- Django tests and `pytest` use PostgreSQL test databases. By default the test DB name is your current `POSTGRES_DB` with `_test` appended, for example `timewise` -> `timewise_test`.

## Docker workflow

Run the full stack from the project root:

```powershell
docker compose up --build
```

Services:

- FastAPI: `http://127.0.0.1:8000`
- Django admin: `http://127.0.0.1:8001/admin/`
- PostgreSQL: `localhost:5432`

Run migrations in Docker:

```powershell
docker compose run --rm admin uv run python manage.py migrate
```

Create a Django superuser in Docker:

```powershell
docker compose run --rm admin uv run python manage.py createsuperuser
```

Notes:

- The compose setup reads `backend/.env/.env`.
- Inside Docker, the database host is forced to `db`, so your local env file can stay the same.
