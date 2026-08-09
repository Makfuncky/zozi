"""Regression tests for the admin_email router W1 (DB-write) rescue.

Guards that ``backend/routers/admin_email.py`` performs NO direct DB write
inside ``create_campaign`` / ``delete_campaign``. The writes are delegated to
``services.comms.email_write_service`` (``create_email_campaign`` /
``delete_email_campaign``), as the architecture contract requires.

Mirrors the audit's W1 detector (AST walk + session-var tracking).
"""

import ast
import pathlib

ROUTER = pathlib.Path(__file__).resolve().parents[1] / "backend" / "routers" / "admin_email.py"

WRITE_VERBS = {
    "add", "add_all", "commit", "flush", "delete", "merge", "execute",
    "begin", "begin_nested", "savepoint",
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


def _func(tree: ast.AST, name: str):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def test_create_campaign_delegates_no_direct_write():
    tree = ast.parse(ROUTER.read_text(encoding="utf-8"))
    target = _func(tree, "create_campaign")
    assert target is not None, "create_campaign must exist"

    session_vars = _session_params(target)
    bad = [(ln, m) for ln, m in _session_calls(target, session_vars) if m in WRITE_VERBS]
    assert not bad, f"direct session write in create_campaign: {bad}"

    # Router must be write-free: it delegates the persistence to a
    # controller/service rather than performing it inline.
    body = ast.dump(target)
    assert "email_ctrl" in body or "create_email_campaign" in body, \
        "must delegate the write to a controller/service"


def test_delete_campaign_delegates_no_direct_write():
    tree = ast.parse(ROUTER.read_text(encoding="utf-8"))
    target = _func(tree, "delete_campaign")
    assert target is not None, "delete_campaign must exist"

    session_vars = _session_params(target)
    bad = [(ln, m) for ln, m in _session_calls(target, session_vars) if m in WRITE_VERBS]
    assert not bad, f"direct session write in delete_campaign: {bad}"

    body = ast.dump(target)
    assert "email_ctrl" in body or "delete_email_campaign" in body, \
        "must delegate the write to a controller/service"
