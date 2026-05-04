import os

import django
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.wsgi import get_wsgi_application  # noqa: E402

from api.registry import register_routers  # noqa: E402

app = FastAPI(title="Timewise API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


register_routers(app)

# Django handles /admin/ and /static/ (via whitenoise middleware).
# This mount must come last — FastAPI routes defined above take priority.
app.mount("/", WSGIMiddleware(get_wsgi_application()))
