"""
Architecture layer dependency enforcement.

Allowed call flow:
    api → orchestrators (optional) → services → repositories

Forbidden imports:
    api:           must not import from repositories
    orchestrators: must not import from api or repositories
    services:      must not import from api or orchestrators
    repositories:  must not import from api, orchestrators, or services

Layer detection relies on directory segment names in the file path and
dotted import paths. Files under 'tests/', '.venv/', 'migrations/', or
'__pycache__/' are excluded from checks.
"""

import ast
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).parents[2]

# Maps path/import segment → canonical layer name
SEGMENT_TO_LAYER: dict[str, str] = {
    "api": "api",
    "orchestrators": "orchestrator",
    "services": "service",
    "repositories": "repository",
}

# For each layer, the set of layers it must NOT import from
FORBIDDEN: dict[str, frozenset[str]] = {
    "api": frozenset({"repository"}),
    "orchestrator": frozenset({"api", "repository"}),
    "service": frozenset({"api", "orchestrator"}),
    "repository": frozenset({"api", "orchestrator", "service"}),
}

_SKIP_SEGMENTS = frozenset({"tests", ".venv", "migrations", "__pycache__"})


def _file_layer(path: Path) -> str | None:
    """Return the layer for a source file, or None if it should be skipped."""
    parts = path.parts
    if _SKIP_SEGMENTS.intersection(parts):
        return None
    for part in parts:
        if part in SEGMENT_TO_LAYER:
            return SEGMENT_TO_LAYER[part]
    return None


def _import_layer(module: str) -> str | None:
    """Return the layer an import belongs to, based on its dotted module path."""
    for segment in module.split("."):
        if segment in SEGMENT_TO_LAYER:
            return SEGMENT_TO_LAYER[segment]
    return None


def _imports(path: Path) -> list[str]:
    """Return all imported module names found in a Python file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def _collect_violations() -> list[str]:
    violations: list[str] = []
    for py_file in BACKEND_ROOT.rglob("*.py"):
        layer = _file_layer(py_file)
        if layer is None:
            continue
        forbidden = FORBIDDEN.get(layer, frozenset())
        for module in _imports(py_file):
            imported_layer = _import_layer(module)
            if imported_layer in forbidden:
                rel = py_file.relative_to(BACKEND_ROOT)
                violations.append(
                    f"{rel}: [{layer}] must not import [{imported_layer}] — '{module}'"
                )
    return violations


def test_architecture_layer_dependencies() -> None:
    """No layer may import from a layer above it in the hierarchy."""
    violations = _collect_violations()
    if violations:
        formatted = "\n".join(f"  {v}" for v in violations)
        pytest.fail(
            f"\n{len(violations)} architecture violation(s) found:\n{formatted}"
        )
