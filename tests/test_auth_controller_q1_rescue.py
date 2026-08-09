"""Q1 rescue test — auth controller.

Guards the Q1 architecture rule: controllers must never reach into the ORM
session directly through ``db.query()`` / ``db.execute()`` / ``db.get()``.
Every DB read is delegated to ``services.db_read`` (the shared data-access
layer), which keeps the controller a thin HTTP/business-logic adapter.
"""
from __future__ import annotations

from q1_rescue_utils import (
    assert_imports_db_read,
    assert_no_session_reads,
)

_AUTH_FILE = "controllers/auth_controller.py"


def test_auth_controller_has_no_session_reads() -> None:
    """Q1: the controller must not call db.query/execute/get directly."""
    assert_no_session_reads(_AUTH_FILE)


def test_auth_controller_delegates_to_db_read() -> None:
    """Read helpers must be imported from the shared services.db_read layer."""
    assert_imports_db_read(_AUTH_FILE)
