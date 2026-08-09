"""W1 regression test for the AI-upload router rescue.

Guards against re-introducing Layer-1 DB writes into the router or
controller layers, verifies the controller->service delegation at
runtime, and that the router delegates to the controller.
"""
from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parent.parent

_EXPECTED_WRITE_VERBS = {
    "add",
    "add_all",
    "commit",
    "flush",
    "delete",
    "merge",
    "bulk_insert_mappings",
    "bulk_save_objects",
    "bulk_update_mappings",
    "begin",
    "begin_nested",
    "savepoint",
}
_SESSION_NAMES = {
    "db",
    "session",
    "db_session",
    "sess",
    "_db",
    "_session",
    "_db_session",
    "_sess",
    "session_scope",
    "db_session_scope",
}


def _find_layer_writes(source: str) -> list[str]:
    tree = ast.parse(source)
    findings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            value = node.func.value
            if isinstance(value, ast.Name) and value.id in _SESSION_NAMES:
                if node.func.attr in _EXPECTED_WRITE_VERBS:
                    findings.append(f"{value.id}.{node.func.attr}")
    return findings


def _isolate_serializers(module, monkeypatch) -> None:
    for name in dir(module):
        if name.startswith("serialize_"):
            monkeypatch.setattr(module, name, lambda *a, **k: {})


@pytest.fixture(scope="module")
def router_src() -> str:
    return (_BACKEND_ROOT / "routers" / "ai_upload.py").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def controller_src() -> str:
    return (
        _BACKEND_ROOT / "controllers" / "ai_upload_controller.py"
    ).read_text(encoding="utf-8")


def test_router_has_no_layer1_writes(router_src: str) -> None:
    assert _find_layer_writes(router_src) == [], "ai_upload router must not call db.<write>"


def test_controller_has_no_layer1_writes(controller_src: str) -> None:
    assert _find_layer_writes(controller_src) == [], (
        "ai_upload controller must not call db.<write>"
    )


def test_router_delegates_to_controller(router_src: str) -> None:
    for fn in ("publish_job", "cancel_job", "create_job", "process_job"):
        assert re.search(rf"\bai_ctrl\.{fn}\s*\(", router_src), (
            f"router must delegate to ai_ctrl.{fn}"
        )


def test_modules_import() -> None:
    importlib.import_module("routers.public_ai_upload_access")
    importlib.import_module("controllers.ai_upload_controller")
    mod = importlib.import_module("services.ai.ai_upload_write_service")
    for fn in (
        "create_ai_upload_job",
        "run_ai_upload_job",
        "process_ai_upload_job",
        "publish_ai_upload_job",
        "cancel_ai_upload_job",
    ):
        assert callable(getattr(mod, fn, None)), f"missing service fn {fn}"


def test_controller_delegates_to_service(monkeypatch) -> None:
    from unittest.mock import MagicMock

    import controllers.ai_upload_controller as ctrl

    _isolate_serializers(ctrl, monkeypatch)

    # The controller binds the service functions under `_`-prefixed names.
    bound = {
        "_create_ai_upload_job": MagicMock(),
        "_publish_ai_upload_job": MagicMock(),
        "_cancel_ai_upload_job": MagicMock(),
        "_process_ai_upload_job": MagicMock(),
    }
    for name, m in bound.items():
        monkeypatch.setattr(ctrl, name, m)

    ctrl.create_job(["img"], "OM", "m", "p", {"user": {"id": 1}}, MagicMock())
    ctrl.publish_job(1, {"2": {"name": "x"}}, {"id": 3}, MagicMock())
    ctrl.cancel_job(5, {"id": 3}, MagicMock())
    ctrl.process_job(42)

    bound["_create_ai_upload_job"].assert_called_once()
    bound["_publish_ai_upload_job"].assert_called_once()
    bound["_cancel_ai_upload_job"].assert_called_once()
    bound["_process_ai_upload_job"].assert_called_once()
