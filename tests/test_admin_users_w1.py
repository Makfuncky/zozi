"""Regression tests for the admin_users router W1 (DB-write) rescue.

These tests guard that ``backend/routers/admin_users.py`` performs NO direct
DB write (or read) inside the ``bulk_toggle_user_active`` route. The write has
been delegated to the ``admin_bulk_toggle_active`` service, exactly as the
architecture contract (routers/controllers must not own DB transactions) requires.

The check mirrors the audit's W1/Q1 detector: it walks the AST, tracks the
session parameter name, and flags any ``session.<write/read verb>()`` call.
"""

import ast
import pathlib

ROUTER = pathlib.Path(__file__).resolve().parents[1] / "backend" / "routers" / "admin_users.py"

WRITE_VERBS = {
    "add", "add_all", "commit", "flush", "delete", "merge", "execute",
}
READ_VERBS = {
    "query", "scalar", "first", "all", "get", "refresh", "execute",
}


def _session_params(func: ast.AST) -> set[str]:
    names = {"db", "session", "sess", "s", "db_session"}
    for arg in func.args.args + func.args.posonlyargs + func.args.kwonlyargs:
        if arg.arg in names:
            names.add(arg.arg)
        elif arg.annotation is not None:
            ann = ast.dump(arg.annotation)
            if "Session" in ann or "AsyncSession" in ann:
                names.add(arg.arg)
    return names


def _session_calls(func: ast.AST, session_vars: set[str]) -> list[tuple[int, str]]:
    hits = []
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        obj = node.func.value
        obj_name = obj.attr if isinstance(obj, ast.Attribute) else getattr(obj, "id", "")
        if obj_name in session_vars:
            hits.append((node.lineno, node.func.attr))
    return hits


def test_bulk_toggle_user_active_imports_service():
    tree = ast.parse(ROUTER.read_text(encoding="utf-8"))
    # import of the service exists
    imported = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for n in node.names:
                if n.name == "admin_bulk_toggle_active":
                    imported = True
    assert imported, "admin_bulk_toggle_active must be imported from services.user.user_profile_service"


def test_bulk_toggle_user_active_has_no_direct_session_write_or_read():
    tree = ast.parse(ROUTER.read_text(encoding="utf-8"))
    target = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "bulk_toggle_user_active":
            target = node
            break
    assert target is not None, "route bulk_toggle_user_active must exist"

    session_vars = _session_params(target)
    calls = _session_calls(target, session_vars)
    bad = [(ln, m) for ln, m in calls if m in WRITE_VERBS or m in READ_VERBS]
    assert not bad, f"direct session write/read in route: {bad}"
