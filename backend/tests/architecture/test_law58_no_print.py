"""Law 58 gate: ``print()`` is forbidden in production code.

R-10 (RUNTIME_PROBLEM.md): six debug ``print()``/``traceback.print_stack()``
calls were found in hot paths — ``infrastructure/utils/config.py`` dumped a
stack trace on *every* process boot, ``modules/admin/routers/staff.py`` printed
object ids at import time, and the login path printed ``user.id`` + e-mail to
stderr (Law 282 PII leak). ``_most_imp_docx/PRODUCTION_READINESS_CHECKLIST.md``
item B-07 tracks the same defect.

This test parses the production packages with ``ast`` and fails on any call to
``print``/``pprint``/``traceback.print_stack``, so the defect class cannot come
back. Tests, scripts and dev tooling are out of scope (Law 58 governs the code
that ships).
"""
from __future__ import annotations

import ast
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))

PRODUCTION_PACKAGES = (
    "modules",
    "domains",
    "rbac",
    "kernel",
    "providers",
    "jobs",
    "middleware",
    "infrastructure",
)
PRODUCTION_ROOT_FILES = ("main.py", "lifespan.py", "config.py")
FORBIDDEN_CALLS = {"print", "pprint"}
_SKIPPED_DIRS = {"tests", "__pycache__", ".venv", "node_modules", "scripts"}


def _python_files():
    for name in PRODUCTION_PACKAGES:
        root = os.path.join(_BACKEND_ROOT, name)
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in _SKIPPED_DIRS]
            for fn in filenames:
                if fn.endswith(".py"):
                    yield os.path.join(dirpath, fn)
    for fn in PRODUCTION_ROOT_FILES:
        path = os.path.join(_BACKEND_ROOT, fn)
        if os.path.isfile(path):
            yield path


def _violations(path: str) -> list[str]:
    with open(path, encoding="utf-8-sig") as fh:
        source = fh.read()
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:  # pragma: no cover — a syntax error fails elsewhere
        return [f"{path}: syntax error: {exc}"]
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name in FORBIDDEN_CALLS:
                found.append(f"{os.path.relpath(path, _BACKEND_ROOT)}:{node.lineno}: {name}()")
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "print_stack"
                and isinstance(func.value, ast.Name)
                and func.value.id == "traceback"
            ):
                found.append(
                    f"{os.path.relpath(path, _BACKEND_ROOT)}:{node.lineno}: traceback.print_stack()"
                )
    return found


def test_no_print_in_production_code():
    offenders: list[str] = []
    for path in _python_files():
        offenders.extend(_violations(path))
    assert not offenders, (
        "Law 58 violation — print()/traceback.print_stack() found in production "
        "code; use structlog instead:\n" + "\n".join(offenders)
    )


def test_production_packages_were_actually_scanned():
    """Guard against the scan silently matching zero files."""
    files = list(_python_files())
    assert len(files) > 200, f"scan only covered {len(files)} files — glob is broken"
