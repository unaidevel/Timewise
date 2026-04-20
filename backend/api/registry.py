import importlib
import pkgutil
from pathlib import Path

from fastapi import FastAPI

APP_GROUPS = ["product", "infra", "shared"]


def register_routers(app: FastAPI) -> None:
    """
    Scan product/, infra/ and shared/ modules and register their FastAPI routers.

    Each <group>/<module>/api/router.py must expose:
    - router: APIRouter
    - PREFIX: str
    - TAGS: list[str]
    """
    backend_root = Path(__file__).resolve().parents[1]

    for group in APP_GROUPS:
        group_path = backend_root / group
        if not group_path.exists():
            continue

        for module_info in pkgutil.iter_modules([str(group_path)]):
            module_path = f"{group}.{module_info.name}.api.router"
            try:
                module = importlib.import_module(module_path)
                app.include_router(module.router)
            except ModuleNotFoundError as exc:
                # If the router module itself does not exist, skip that app.
                # If an internal dependency is missing, surface the real error.
                if exc.name == module_path:
                    continue
                raise ModuleNotFoundError(
                    f"Failed importing {module_path}. Missing dependency: {exc.name}"
                ) from exc
            except AttributeError as exc:
                raise AttributeError(
                    f"{module_path} must define 'router'. {exc}"
                ) from exc
