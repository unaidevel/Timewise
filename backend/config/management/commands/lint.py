import subprocess
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Run Ruff checks and auto-fix formatting or lint issues when possible."

    def handle(self, *args, **options):
        backend_root = Path(__file__).resolve().parents[3]

        lint_check = [sys.executable, "-m", "ruff", "check", "."]
        format_check = [sys.executable, "-m", "ruff", "format", "--check", "."]

        lint_result = self._run_subprocess(
            lint_check,
            backend_root,
            "Ruff lint check failed.",
            raise_on_error=False,
        )
        format_result = self._run_subprocess(
            format_check,
            backend_root,
            "Ruff format check failed.",
            raise_on_error=False,
        )

        if lint_result == 0 and format_result == 0:
            self.stdout.write(self.style.SUCCESS("Ruff checks already pass."))
            return

        self.stdout.write("Applying Ruff fixes...")
        self._run_subprocess(
            [sys.executable, "-m", "ruff", "check", ".", "--fix"],
            backend_root,
            "Ruff was unable to apply lint fixes.",
        )
        self._run_subprocess(
            [sys.executable, "-m", "ruff", "format", "."],
            backend_root,
            "Ruff was unable to format the codebase.",
        )

        self.stdout.write("Re-running Ruff checks...")
        self._run_subprocess(lint_check, backend_root, "Ruff lint check still fails.")
        self._run_subprocess(
            format_check,
            backend_root,
            "Ruff format check still fails.",
        )

        self.stdout.write(self.style.SUCCESS("Ruff checks pass after auto-fixing."))

    def _run_subprocess(
        self,
        command: list[str],
        cwd: Path,
        error_message: str,
        raise_on_error: bool = True,
    ) -> int:
        completed = subprocess.run(command, cwd=cwd, check=False)
        if completed.returncode != 0 and raise_on_error:
            raise CommandError(error_message)
        return completed.returncode
