import os

import django
from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = FastAPI(title="Portfolio API")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


# Django handles /admin/ and /static/ (via whitenoise middleware).
# This mount must come last — FastAPI routes defined above take priority.
app.mount("/", WSGIMiddleware(get_wsgi_application()))
