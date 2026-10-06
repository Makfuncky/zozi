"""Paired test for Stage-1 resolver B-06.

Law 21 (timestamp server_default), Law 31 (no providers/ import in domain
models), and the no-providers structural check for:

* ``backend/domains/comms/models/chat.py``
* ``backend/domains/comms/models/marketing.py``

The AST walk descends into every ``ast.ClassDef`` body and covers **both**
``ast.Assign`` and ``ast.AnnAssign`` so the blind-spot that let 40 similar
defects survive elsewhere in this repo cannot hide here.

Every ``created_at`` / ``updated_at`` column declaration must carry
``server_default=func.now()``.  A Python-side ``default=`` alongside the
``server_default`` is tolerated (surrounding style does it), but a column
with **neither** ``server_default`` nor a ``now()``-bearing expression is a
Law 21 violation.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[3]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

TARGET_FILES = [
    BACKEND_ROOT / "domains" / "comms" / "models" / "chat.py",
    BACKEND_ROOT / "domains" / "comms" / "models" / "marketing.py",
]


def _is_timestamp_target(target: ast.expr) -> bool:
    """Return True if the assignment target is created_at or updated_at."""
    if isinstance(target, ast.Name):
        return target.id in ("created_at", "updated_at")
    return False


def _call_is_func_now(node: ast.AST) -> bool:
    """Return True if the node represents ``func.now()``."""
    if not isinstance(node, ast.Call):
        return False
    func_node = node.func
    if isinstance(func_node, ast.Attribute):
        return func_node.attr == "now"
    if isinstance(func_node, ast.Name):
        return func_node.id == "now"
    return False


def _kw_has_func_now(kw: ast.keyword) -> bool:
    return _call_is_func_now(kw.value)


def _has_server_default_now(keywords: list[ast.keyword]) -> bool:
    """Return True if any keyword is ``server_default=func.now()``."""
    return any(kw.arg == "server_default" and _call_is_func_now(kw.value) for kw in keywords)


def _has_func_now_default(keywords: list[ast.keyword]) -> bool:
    """Return True if any keyword is ``default=func.now()``."""
    return any(kw.arg == "default" and _call_is_func_now(kw.value) for kw in keywords)


def _collect_timestamp_columns(source: str, module_name: str) -> list[dict]:
    """Walk class bodies and return every created_at / updated_at Column()."""
    columns = []
    tree = ast.parse(source)
    for class_node in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
        for item in class_node.body:
            if isinstance(item, ast.Assign):
                targets = item.targets
                value = item.value
            elif isinstance(item, ast.AnnAssign):
                targets = [item.target]
                value = item.value
            else:
                continue

            if not isinstance(value, ast.Call):
                continue
            for target in targets:
                if not _is_timestamp_target(target):
                    continue
                keywords = value.keywords
                has_server_default = _has_server_default_now(keywords)
                has_python_default = _has_func_now_default(keywords)
                columns.append(
                    {
                        "class": class_node.name,
                        "name": target.id,  # type: ignore[union-attr]
                        "has_server_default": has_server_default,
                        "has_python_default": has_python_default,
                        "lineno": item.lineno,
                    }
                )
    return columns


def _assert_no_providers_import(source: str, path: Path) -> None:
    """Assert the module does not import from providers/."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("providers"):
                raise AssertionError(
                    f"{path}: import from providers/ found: {node.module}"
                )
            if node.module and node.module.split(".")[0] == "providers":
                raise AssertionError(
                    f"{path}: import from providers/ found: {node.module}"
                )


def test_timestamp_columns_carry_server_default_func_now():
    """Law 21 — every created_at / updated_at must have server_default=func.now()."""
    all_offenders = []
    for path in TARGET_FILES:
        source = path.read_text(encoding="utf-8")
        columns = _collect_timestamp_columns(source, path.stem)
        for col in columns:
            if not col["has_server_default"]:
                all_offenders.append(
                    f"{path.name}:{col['lineno']} {col['class']}.{col['name']} "
                    f"missing server_default=func.now()"
                )
    assert not all_offenders, (
        f"Law 21 violations in {len(all_offenders)} column(s):\n  "
        + "\n  ".join(all_offenders)
    )


def test_neither_module_imports_from_providers():
    """Law 31 — domain models must not import from providers/."""
    for path in TARGET_FILES:
        source = path.read_text(encoding="utf-8")
        _assert_no_providers_import(source, path)
