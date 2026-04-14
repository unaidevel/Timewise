import os

import django
from fastapi import FastAPI

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

app = FastAPI(title="Portfolio API")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
