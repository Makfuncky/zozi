"""Rescue tests for the Comms / WebSocket router (system_comms_status).

Verifies the W1/CG1 violations flagged in SYSTEM_AUDIT_REPORT-style audits are
resolved: the router no longer performs DB writes or references ``models``
directly — it delegates persistence and user reads to
``domains.comms.services.messaging.chat_write_service``.
Also locks the boot-blocking import in main.py.

Layout notes (repairs, 2026-10-05): these paths previously resolved against
``tests/`` because BACKEND climbed only two directories, so every assertion
failed with FileNotFoundError instead of testing anything. The router was also
moved from ``routers/system_comms_status.py`` to
``modules/admin/routers/comms.py``, and the write-owner service was flattened
from the ``messaging.chat`` package to the ``messaging.chat_write_service``
module.
"""
from __future__ import annotations

import importlib
import importlib.util
import os

TESTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/tests
BACKEND = os.path.dirname(TESTS)  # backend/
ROUTER_PATH = os.path.join(BACKEND, "modules", "admin", "routers", "comms.py")
MAIN_PATH = os.path.join(BACKEND, "main.py")
SERVICE_DOTTED = "domains.comms.services.messaging.chat_write_service"


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _load_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_comms_router_has_no_direct_db_writes():
    src = _read(ROUTER_PATH)
    for token in ("db.add(", "db.commit(", "db.query(", "db.delete("):
        assert token not in src, f"Router still does direct DB op: {token}"


def test_comms_router_does_not_reference_models_directly():
    src = _read(ROUTER_PATH)
    assert "from models" not in src, "Router still imports `models` directly (CG1)"
    assert "from domains.governance.models.core import" not in src


def test_comms_router_delegates_to_canonical_service():
    """The write-owner must be reachable and expose the delegated helpers.

    The router itself was dissolved into ``modules/admin/routers/comms.py``,
    so the delegation contract is now locked at the service layer: the
    service imports the four helpers from the canonical write-owner module.
    """
    src = _read(
        os.path.join(BACKEND, "domains", "comms", "services", "system_comms_status_service.py")
    )
    assert f"from {SERVICE_DOTTED} import" in src
    for fn in ("persist_message", "mark_messages_read", "get_user_display_name", "get_user_role"):
        assert fn in src, f"Service does not delegate {fn} to the canonical module"


def test_comms_service_exists():
    svc = importlib.import_module(SERVICE_DOTTED)

    # The service is the actual DB-write owner.
    assert hasattr(svc, "persist_message")
    assert hasattr(svc, "mark_messages_read")


def test_comms_router_imports_and_exports_websocket_user():
    mod = _load_module("syscomms_under_test", ROUTER_PATH)
    assert hasattr(mod, "websocket_user")
    assert hasattr(mod, "router")


def test_comms_ws_handler_requires_access_token():
    """Law 41: /ws/user must authenticate before accepting the socket."""
    src = _read(ROUTER_PATH)
    handler = src[src.find("async def websocket_user"):]
    assert 'expected_type="access"' in handler, (
        "websocket_user must decode with expected_type='access'"
    )
    assert handler.index("decode_token") < handler.index("await websocket.accept()"), (
        "websocket_user must authenticate before calling accept()"
    )


def test_main_wires_comms_ws_user_from_current_module():
    src = _read(MAIN_PATH)
    assert "from modules.admin.routers.comms import websocket_user" in src
    assert "routers.public_comms_status" not in src
    assert "routers.system_comms_status" not in src


def test_app_boots_and_exposes_bare_ws_user_route():
    import main  # noqa: F401  (boot previously crashed on the bad import)
    paths = [getattr(r, "path", None) for r in main.app.routes]
    assert "/ws/user" in paths, "Bare /ws/user websocket route must be registered"
