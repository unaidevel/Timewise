# Backend Overview

The backend uses **FastAPI** as the HTTP layer and **Django** exclusively for ORM, models, and migrations. This separation keeps the web framework decoupled from the data layer.

## Package management

Dependencies are managed with `uv`. All commands run through `uv run` to use the project's virtual environment without activating it manually.

```bash
uv sync
```

## Running the app

```bash
uv run uvicorn main:app --reload
```

## Common commands

| Command | Description |
|---|---|
| `uv run pytest` | Run all tests |
| `uv run python manage.py lint` | Run Ruff linter |
| `uv run python manage.py testall` | Run Django + pytest suite |
| `uv run python manage.py testall --coverage` | With coverage report |
| `uv run ruff check .` | Check linting without fixing |
| `uv run python manage.py makemigrations` | Generate new migrations |
| `uv run python manage.py migrate` | Apply migrations |

## Environment variables

Variables are loaded from the following files in order:

- `backend/.env/global.env`
- `backend/.env/auth.env`
- `backend/.env/.env`
- `backend/.env/.env.local`

Copy the example file to get started:

```bash
cp backend/.env/.env.example backend/.env/.env
```

## Docker

Run the full stack from the project root:

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| FastAPI | http://127.0.0.1:8000 |
| Django admin | http://127.0.0.1:8001/admin/ |
| PostgreSQL | localhost:5432 |

```bash
# Run migrations
docker compose run --rm admin uv run python manage.py migrate

# Create superuser
docker compose run --rm admin uv run python manage.py createsuperuser
```
