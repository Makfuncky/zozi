"""Verify the comms-domain W1 refactor.

The four comms routers (tickets, push_notifications, email, ws_chat) must no
longer call session write verbs (db.add/commit/delete/flush/...) directly;
those writes now live in ``services/comms/*`` behind thin controllers. This
mirrors the auditor's W1 detection so we can assert the violation is cleared.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

BACKEND = pathlib.Path(__file__).resolve().parents[1] / "backend"
ROUTERS = BACKEND / "routers"

WRITE_VERBS = {
    "add", "add_all", "commit", "flush", "delete", "merge",
    "bulk_insert_mappings", "bulk_save_objects", "bulk_update_mappings",
    "begin", "begin_nested", "savepoint",
}
SESSION_NAMES = {"db", "session", "sess", "s", "db_session"}

TARGETS = ["tickets.py", "push_notifications.py", "email.py", "ws_chat.py"]


def _router_write_lines(path: pathlib.Path) -> list[int]:
    tree = ast.parse(path.read_text())
    session_vars = set(SESSION_NAMES)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                if arg.arg in SESSION_NAMES:
                    session_vars.add(arg.arg)
                elif arg.annotation:
                    ann = ast.dump(arg.annotation)
                    if "Session" in ann or "AsyncSession" in ann:
                        session_vars.add(arg.arg)
    hits: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            obj = node.func.value
            obj_name = obj.id if isinstance(obj, ast.Name) else (obj.attr if isinstance(obj, ast.Attribute) else "")
            if obj_name in session_vars and node.func.attr in WRITE_VERBS:
                hits.append(node.lineno)
    return hits


@pytest.mark.parametrize("name", TARGETS)
def test_router_has_no_session_writes(name: str):
    hits = _router_write_lines(ROUTERS / name)
    assert hits == [], f"{name} still writes to the session at lines {hits}"


def test_import_chain_resolves():
    # Routers -> controllers -> services must all import cleanly.
    import controllers.comms.tickets_controller  # noqa: F401
    import controllers.comms.push_notifications_controller  # noqa: F401
    import controllers.comms.email_admin_controller  # noqa: F401
    import controllers.comms.chat_write_controller  # noqa: F401
    import routers.public_tickets_management  # noqa: F401
    import routers.public_push_notifications_access  # noqa: F401
    import routers.public_email_access  # noqa: F401
    import routers.public_ws_chat_access  # noqa: F401
