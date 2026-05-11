# Getting Started — Backend

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (package manager)
- PostgreSQL (or Docker)

## Local setup (without Docker)

**1. Install dependencies**

```bash
cd backend
uv sync
```

**2. Configure environment**

```bash
cp .env/.env.example .env/.env
# Fill in your PostgreSQL credentials
```

**3. Run migrations**

```bash
uv run python manage.py migrate
```

**4. Start the server**

```bash
uv run uvicorn main:app --reload
```

The API is now available at `http://localhost:8000` and the interactive docs at `http://localhost:8000/docs`.

## Docker setup

From the project root:

```bash
docker compose up --build
docker compose run --rm admin uv run python manage.py migrate
```

## Running tests

```bash
uv run python manage.py testall           # Django + pytest
uv run python manage.py testall --coverage  # with coverage
```

The test suite requires a running PostgreSQL instance. The test database is created automatically as `<POSTGRES_DB>_test`.

## Pre-commit hooks

Install the hooks once after cloning:

```bash
uv run pre-commit install
```

Hooks run Ruff (lint + format) and enforce conventional commit messages on every commit.
