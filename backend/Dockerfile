FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock* ./

RUN pip install --no-cache-dir uv
RUN uv sync --no-dev

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uv run python manage.py migrate --no-input && uv run python manage.py collectstatic --no-input && uv run uvicorn main:app --host 0.0.0.0 --port 8000"]
