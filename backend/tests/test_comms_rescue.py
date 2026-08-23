"""Rescue tests for the Comms / WebSocket router (system_comms_status).

Verifies the W1/CG1 violations flagged in SYSTEM_AUDIT_REPORT-style audits are
resolved: the router no longer performs DB writes or references ``models``
directly — it delegates persistence and user reads to
``controllers.comms.chat_write_controller`` -> ``services.comms.chat_write_service``.
Also locks the boot-blocking import in main.py (was pointing at the pre-rename
name ``public_comms_status``).
"""
from __future__ import annotations

import importlib.util
import os

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTER_PATH = os.path.join(BACKEND, "routers", "system_comms_status.py")
MAIN_PATH = os.path.join(BACKEND, "main.py")


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


def test_comms_router_delegates_to_canonical_controller():
    src = _read(ROUTER_PATH)
    assert "from modules.comms.routers.chat_write_controller import" in src
    for fn in ("persist_message", "mark_messages_read", "get_user_display_name", "get_user_role"):
        assert fn in src, f"Router does not delegate {fn} to the controller"


def test_comms_controller_wires_canonical_service():
    import modules.comms.routers.chat_write_controller as ctrl
    import domains.comms.services.chat_write_service as svc

    # Controller re-exports the same call contract the router uses.
    assert hasattr(ctrl, "persist_message")
    assert hasattr(ctrl, "mark_messages_read")
    # The service is the actual DB-write owner.
    assert hasattr(svc, "persist_message")
    assert hasattr(svc, "mark_messages_read")


def test_comms_router_imports_and_exports_websocket_user():
    mod = _load_module("syscomms_under_test", ROUTER_PATH)
    assert hasattr(mod, "websocket_user")
    assert hasattr(mod, "router")


def test_main_wires_system_comms_status_not_old_name():
    src = _read(MAIN_PATH)
    assert "routers.system_comms_status import websocket_user" in src
    assert "routers.public_comms_status" not in src


def test_app_boots_and_exposes_bare_ws_user_route():
    import main  # noqa: F401  (boot previously crashed on the bad import)
    paths = [getattr(r, "path", None) for r in main.app.routes]
    assert "/ws/user" in paths, "Bare /ws/user websocket route must be registered"
