"""Q1 rescue test — controllers/supplier_controller.py.

Guards the Q1 architecture rule: controllers must NOT call ``db.query()`` /
``db.execute()`` / ``db.get()`` directly. All read access is delegated to
``services.db_read``.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_ROOT = _REPO_ROOT / "backend"
for _p in (str(_BACKEND_ROOT), str(_REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

from q1_rescue_utils import (  # noqa: E402
    assert_imports_db_read,
    assert_no_session_reads,
)

_TARGET = "controllers/supplier_controller.py"


def test_controller_module_importable() -> None:
    assert importlib.import_module("controllers.supplier_controller") is not None


def test_db_read_layer_importable() -> None:
    importlib.import_module("services.db_read")


def test_controller_has_no_direct_session_reads() -> None:
    assert_no_session_reads(_TARGET)


def test_controller_delegates_to_db_read() -> None:
    assert_imports_db_read(_TARGET)


def test_db_read_helpers_are_callable() -> None:
    db_read = importlib.import_module("services.db_read")
    for name in ("all_rows", "first", "count", "scalar_with_filters", "aggregate_rows"):
        assert callable(getattr(db_read, name, None)), f"missing helper {name}"
