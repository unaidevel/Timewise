import os

import django
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.middleware.wsgi import WSGIMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings  # noqa: E402
from django.core.wsgi import get_wsgi_application  # noqa: E402

from api.registry import register_routers  # noqa: E402
from infra.common.rate_limiting import (  # noqa: E402
    limiter,
    rate_limit_exceeded_handler,
)

app = FastAPI(title="Timewise API", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_ALLOWED_METHODS,
    allow_headers=settings.CORS_ALLOWED_HEADERS,
)


register_routers(app)

# Django handles /admin/ and /static/ (via whitenoise middleware).
# This mount must come last — FastAPI routes defined above take priority.
app.mount("/", WSGIMiddleware(get_wsgi_application()))
