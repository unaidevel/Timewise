import importlib
import os
import subprocess
import sys
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from config.testing import drop_postgres_test_database_if_exists

_WIDTH = 60


class Command(BaseCommand):
    help = "Run all non-API Django tests and all API pytest suites."

    def add_arguments(self, parser):
        parser.add_argument(
            "--coverage",
            action="store_true",
            help="Run both suites under coverage and generate coverage reports.",
        )
        parser.add_argument(
            "--keepdb",
            action="store_true",
            help="Preserve the test databases between runs.",
        )
        parser.add_argument(
            "--dropdb",
            action="store_true",
            help="Drop existing test databases before running the suites.",
        )
        parser.add_argument(
            "--skip-architecture",
            action="store_true",
            help="Skip the architecture tests (useful in CI where they run as a separate job).",
        )

    def handle(self, *args, **options):
        if options["keepdb"] and options["dropdb"]:
            raise CommandError("--keepdb and --dropdb cannot be used together.")

        backend_root = Path(__file__).resolve().parents[3]
        django_targets = self._discover_django_test_targets(backend_root)
        pytest_targets = self._discover_pytest_targets(backend_root)

        env = os.environ.copy()
        env["DJANGO_SETTINGS_MODULE"] = "config.test_settings"
        if options["keepdb"]:
            env["TESTALL_KEEPDB"] = "1"
        else:
            env.pop("TESTALL_KEEPDB", None)

        if options["dropdb"]:
            env["TESTALL_DROPDB"] = "1"
            drop_postgres_test_database_if_exists()
        else:
            env.pop("TESTALL_DROPDB", None)

        results: list[tuple[str, bool, float]] = []

        # Architecture tests — always first, no coverage instrumentation
        if not options["skip_architecture"]:
            results.append(
                self._run_suite(
                    "Architecture",
                    [sys.executable, "-m", "pytest", "infra/common/test_architecture.py"],
                    backend_root,
                    env,
                )
            )

        if not django_targets and not pytest_targets:
            self.stdout.write("No Django or API tests were discovered.")
            self._print_summary(results)
            if any(not passed for _, passed, _ in results):
                raise CommandError("One or more test suites failed.")
            return

        if options["coverage"]:
            self._run_subprocess(
                [sys.executable, "-m", "coverage", "erase"],
                backend_root,
                env,
                "Coverage initialization failed.",
            )

        if django_targets:
            django_command = self._django_test_command(options["verbosity"], options)
            if options["keepdb"]:
                django_command.append("--keepdb")
            results.append(
                self._run_suite(
                    "Django",
                    [*django_command, *django_targets],
                    backend_root,
                    env,
                )
            )

        if pytest_targets:
            results.append(
                self._run_suite(
                    "API",
                    self._pytest_command(options["verbosity"], options, pytest_targets),
                    backend_root,
                    env,
                )
            )

        if options["coverage"]:
            self._run_subprocess(
                [sys.executable, "-m", "coverage", "combine"],
                backend_root,
                env,
                "Coverage combine failed.",
            )
            self._run_subprocess(
                [sys.executable, "-m", "coverage", "xml"],
                backend_root,
                env,
                "Coverage XML generation failed.",
            )
            self._run_subprocess(
                [sys.executable, "-m", "coverage", "report", "-m"],
                backend_root,
                env,
                "Coverage report generation failed.",
            )

        self._print_summary(results)

        if any(not passed for _, passed, _ in results):
            raise CommandError("One or more test suites failed.")

    def _run_suite(
        self,
        name: str,
        command: list[str],
        cwd: Path,
        env: dict[str, str],
    ) -> tuple[str, bool, float]:
        self.stdout.write(f"\n{'─' * _WIDTH}")
        self.stdout.write(f"  {name.upper()}")
        self.stdout.write(f"{'─' * _WIDTH}")

        start = time.monotonic()
        completed = subprocess.run(command, cwd=cwd, env=env, check=False)
        duration = time.monotonic() - start
        passed = completed.returncode == 0

        if passed:
            self.stdout.write(self.style.SUCCESS(f"\n  ✓  {name}  ({duration:.1f}s)"))
        else:
            self.stdout.write(
                self.style.ERROR(f"\n  ✗  {name}  ({duration:.1f}s)  ← FAILED")
            )

        return (name, passed, duration)

    def _print_summary(self, results: list[tuple[str, bool, float]]) -> None:
        self.stdout.write(f"\n{'═' * _WIDTH}")
        self.stdout.write("  RESULTS")
        self.stdout.write(f"{'═' * _WIDTH}")

        for name, passed, duration in results:
            if passed:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓  {name:<20} {duration:.1f}s")
                )
            else:
                self.stdout.write(self.style.ERROR(f"  ✗  {name:<20} {duration:.1f}s"))

        passed_count = sum(1 for _, p, _ in results if p)
        failed_count = len(results) - passed_count

        self.stdout.write("")
        if failed_count == 0:
            self.stdout.write(
                self.style.SUCCESS(f"  All {passed_count} suite(s) passed.")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"  {passed_count} passed · {failed_count} failed")
            )
        self.stdout.write(f"{'═' * _WIDTH}\n")

    def _discover_django_test_targets(self, backend_root: Path) -> list[str]:
        targets: set[str] = set()

        for app_label in self._project_apps():
            app_path = self._resolve_app_path(app_label)
            tests_dir = app_path / "tests"

            if tests_dir.is_dir():
                for test_file in tests_dir.glob("test*.py"):
                    if test_file.is_file():
                        targets.add(str(test_file.relative_to(backend_root)))

                for child in tests_dir.iterdir():
                    if child.name in {"api", "__pycache__"}:
                        continue

                    if child.is_dir() and self._has_test_files(child):
                        targets.add(str(child.relative_to(backend_root)))

            app_tests_file = app_path / "tests.py"
            if app_tests_file.is_file():
                targets.add(str(app_tests_file.relative_to(backend_root)))

        return sorted(targets)

    def _discover_pytest_targets(self, backend_root: Path) -> list[str]:
        targets: set[str] = set()

        for app_label in self._project_apps():
            app_path = self._resolve_app_path(app_label)
            api_tests_dir = app_path / "tests" / "api"

            if not api_tests_dir.is_dir():
                continue

            has_api_tests = any(
                test_file.is_file() and "__pycache__" not in test_file.parts
                for test_file in api_tests_dir.rglob("test*.py")
            )
            if not has_api_tests:
                continue

            targets.add(str(api_tests_dir.relative_to(backend_root)))

        return sorted(targets)

    def _has_test_files(self, path: Path) -> bool:
        return any(
            test_file.is_file() and "__pycache__" not in test_file.parts
            for test_file in path.rglob("test*.py")
        )

    def _pytest_verbosity_args(self, verbosity: int) -> list[str]:
        if verbosity <= 0:
            return ["-q"]
        if verbosity == 1:
            return []
        return ["-" + ("v" * verbosity)]

    def _django_test_command(self, verbosity: int, options) -> list[str]:
        base_command = [sys.executable]
        if options["coverage"]:
            base_command.extend(["-m", "coverage", "run", "--parallel-mode"])

        base_command.extend(["manage.py", "test", f"--verbosity={verbosity}"])
        return base_command

    def _pytest_command(
        self,
        verbosity: int,
        options,
        pytest_targets: list[str],
    ) -> list[str]:
        command = [sys.executable]
        if options["coverage"]:
            command.extend(["-m", "coverage", "run", "--parallel-mode"])

        command.extend(
            [
                "-m",
                "pytest",
                *self._pytest_verbosity_args(verbosity),
                *pytest_targets,
            ]
        )
        return command

    def _project_apps(self) -> list[str]:
        return [
            app_label
            for app_label in settings.INSTALLED_APPS
            if "." in app_label and not app_label.startswith("django.")
        ]

    def _resolve_app_path(self, app_label: str) -> Path:
        module = importlib.import_module(app_label)
        module_file = getattr(module, "__file__", None)
        if module_file is None:
            raise CommandError(
                f"Could not resolve filesystem path for app '{app_label}'."
            )
        return Path(module_file).resolve().parent

    def _run_subprocess(
        self,
        command: list[str],
        cwd: Path,
        env: dict[str, str],
        error_message: str,
    ) -> None:
        completed = subprocess.run(command, cwd=cwd, env=env, check=False)
        if completed.returncode != 0:
            raise CommandError(error_message)
