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
uv run ruff check .
```

## Notes

- Prefer `uv run ...` instead of calling `.venv\Scripts\python.exe` directly.
- `manage.py` still works because Django needs settings for ORM and migrations.
- `core/settings.py` is intentionally minimal because FastAPI is the web layer.
