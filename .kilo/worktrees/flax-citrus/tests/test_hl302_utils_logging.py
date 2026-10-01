"""Regression tests locking in the HL302 (swallowed exception) resolution for
the backend/utils/ module.

Audit rule (scripts/system_trackers/system_architecture_audit.py): an
``except`` handler is "swallowed" (HL302) when its body is only ``pass`` OR
contains no Call whose dotted name includes "log". These tests mirror that
detector for the previously-flagged files and assert no swallowed handlers
remain, so a future edit cannot silently reintroduce the finding.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"

# The 13 utils/ files the audit flagged HL302 (fixed: logging added to every
# un-logged handler). 4 are now fully clean; 9 re-classified to HL303
# (broad-but-logged) which is the correct, logged state.
FORMERLY_HL302_UTILS = [
    "auth.py",
    "backup.py",
    "circuit_breaker.py",
    "config.py",
    "dependencies.py",
    "error_handler.py",
    "ip_utils.py",
    "middleware_helpers.py",
    "money.py",
    "order_tracking.py",
    "prometheus_setup.py",
    "redis_client.py",
    "soft_delete.py",
]


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def _swallowed_lines(source: str) -> list[int]:
    """Mirror the audit's HL302 detector: return lines of swallowed handlers."""
    tree = ast.parse(source)
    swallowed: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        only_pass = all(isinstance(s, ast.Pass) for s in node.body)
        has_log = any(
            isinstance(c, ast.Call) and "log" in _dotted_name(c.func).lower()
            for c in ast.walk(node)
        )
        if only_pass or not has_log:
            swallowed.append(node.lineno)
    return swallowed


def test_utils_files_have_no_swallowed_exceptions():
    """HL302: no ``except`` handler in the fixed utils files may swallow."""
    offenders: list[str] = []
    for name in FORMERLY_HL302_UTILS:
        path = BACKEND / "utils" / name
        if not path.exists():
            continue
        swallowed = _swallowed_lines(path.read_text(encoding="utf-8", errors="replace"))
        if swallowed:
            offenders.append(f"utils/{name}: lines {swallowed}")
    assert not offenders, "swallowed exceptions re-introduced in:\n" + "\n".join(offenders)


def test_utils_files_compile():
    """Every fixed utils file must still byte-compile (incl. __future__ order)."""
    for name in FORMERLY_HL302_UTILS:
        path = BACKEND / "utils" / name
        if not path.exists():
            continue
        compile(path.read_text(encoding="utf-8", errors="replace"), str(path), "exec")


def test_utils_loggers_exist():
    """Files that gained logging must have a module-level logger defined."""
    for name in FORMERLY_HL302_UTILS:
        path = BACKEND / "utils" / name
        if not path.exists():
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        assert re.search(
            r"^(?:logger|log)\s*=\s*(?:logging|structlog)\.get(?:Logger|_logger)\b",
            source,
            flags=re.MULTILINE,
        ), f"utils/{name} lost its module logger"
