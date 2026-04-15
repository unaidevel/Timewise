import importlib
import pkgutil
from pathlib import Path

from fastapi import FastAPI

# Grupos donde viven las apps. El registry los escanea en orden.
APP_GROUPS = ["product", "infra", "shared"]


def register_routers(app: FastAPI) -> None:
    """
    Escanea cada grupo (product/, platform/, shared/) buscando módulos
    que tengan api/router.py. Si lo tienen, registra su router automáticamente.

    Convención que debe seguir cada api/router.py:
        router: APIRouter
        PREFIX: str   — e.g. "/api/v1/workforce"
        TAGS: list[str]
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
                app.include_router(
                    module.router,
                    prefix=module.PREFIX,
                    tags=module.TAGS,
                )
            except ModuleNotFoundError:
                # La app no tiene api/router.py todavía — se ignora
                continue
            except AttributeError as e:
                # El router.py existe pero le falta PREFIX o TAGS
                raise AttributeError(
                    f"{module_path} must define 'router', 'PREFIX' and 'TAGS'. {e}"
                )
