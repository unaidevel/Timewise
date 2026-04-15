from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Creates a new app with the project structure"

    def add_arguments(self, parser):
        parser.add_argument("name", help="Name of the app")
        parser.add_argument("directory", nargs="?", help="Optional destination directory")

    def handle(self, **options):
        app_name = options["name"]
        base = Path(options["directory"]) if options["directory"] else Path.cwd() / app_name

        if base.exists():
            raise CommandError(f"Directory '{base}' already exists.")

        camel = "".join(word.title() for word in app_name.split("_"))

        files = {
            "__init__.py": "",
            "models.py": "from django.db import models\n",
            "admin.py": "from django.contrib import admin\n",
            "api/__init__.py": "",
            "api/router.py": (
                "from fastapi import APIRouter\n\n"
                f'router = APIRouter(prefix="/{app_name}", tags=["{app_name}"])\n'
            ),
            "services/__init__.py": "",
            f"services/{app_name}_service.py": f"class {camel}Service:\n    pass\n",
            "repositories/__init__.py": "",
            f"repositories/{app_name}_repository.py": f"class {camel}Repository:\n    pass\n",
            "tests/__init__.py": "",
            "tests/api/__init__.py": "",
            f"tests/api/test_{app_name}_api.py": "",
            "tests/services/__init__.py": "",
            f"tests/services/test_{app_name}_service.py": "",
            "tests/repositories/__init__.py": "",
            f"tests/repositories/test_{app_name}_repository.py": "",
        }

        for relative_path, content in files.items():
            file = base / relative_path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(content)

        self._register_app(app_name)
        self.stdout.write(self.style.SUCCESS(f"App '{app_name}' created at {base}"))

    def _register_app(self, app_name: str) -> None:
        settings_path = Path(__file__).resolve().parents[3] / "config" / "settings.py"
        source = settings_path.read_text(encoding="utf-8")

        marker = "INSTALLED_APPS = ["
        if marker not in source:
            self.stdout.write(self.style.WARNING("Could not find INSTALLED_APPS in settings.py — add it manually."))
            return

        insertion = f'    "{app_name}",\n'
        updated = source.replace(marker, marker + "\n" + insertion.rstrip("\n"), 1)
        settings_path.write_text(updated, encoding="utf-8")
