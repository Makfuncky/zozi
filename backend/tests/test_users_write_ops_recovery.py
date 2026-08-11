"""Verification tests for the recovered admin user-write operations.

These guard the remediation that restored 9 functions (lost when commit
3d1f49a replaced their real implementations with ``_missing_symbol`` stubs)
into ``services.users.user_write_ops`` and re-exported them from the
``services.users.users_write_service`` shim. The tests assert that the symbols are
real implementations (not stubs), that the shim resolves them, and that the
core deletion/protection logic behaves correctly.
"""
from __future__ import annotations

import pytest

import services.users.user_write_ops as ops
import services.users.users_write_service as shim
import controllers.customer.users as users_ctrl
from models import User

_RECOVERED_NAMES = [
    "_build_user_delete_blocker",
    "_delete_order_records",
    "_hard_delete_user_record",
    "create_chatbot_query_event",
    "create_staff_user",
    "force_reset_password",
    "update_bank_account_verification",
    "update_staff_user",
    "update_user_browsing_history",
]

_LAZY_SHIM_NAMES = [
    "delete_bank_account_record",
    "toggle_user_active",
    "update_user_role",
]


@pytest.mark.parametrize("name", _RECOVERED_NAMES)
def test_recovered_symbol_is_real_function(name):
    obj = getattr(ops, name)
    assert callable(obj), f"{name} should be a real callable, not a stub"
    # ``_missing_symbol`` stubs raise NotImplementedError on access; this
    # guards against a regression that re-introduces the stub.
    assert not getattr(obj, "__name__", "").startswith("_missing_symbol")
    assert "_missing_symbol" not in getattr(obj, "__qualname__", "")


def test_shim_reexports_recovered_symbols():
    for name in _RECOVERED_NAMES:
        assert getattr(shim, name) is getattr(ops, name), (
            f"shim.{name} must resolve to the recovered impl in user_write_ops"
        )


@pytest.mark.parametrize("name", _LAZY_SHIM_NAMES)
def test_shim_lazy_reexports_controller_functions(name):
    assert getattr(shim, name) is getattr(users_ctrl, name), (
        f"shim.{name} must lazily resolve to controllers.customer.users.{name}"
    )


def test_shim_has_no_missing_symbol_stub():
    assert not hasattr(shim, "_missing_symbol")
    for name in _RECOVERED_NAMES + _LAZY_SHIM_NAMES:
        assert "_missing_symbol" not in getattr(shim, name).__qualname__, (
            f"shim.{name} must not be a _missing_symbol stub"
        )


class _FakeUser:
    def __init__(self, user_id, email):
        self.id = user_id
        self.email = email


def test_build_user_delete_blocker_blocks_protected_email(db_session):
    protected = _FakeUser(1, "admin@zozi.com")
    result = build_user_delete_blocker._build_user_delete_blocker(
        protected, {"id": 2}, db_session, delete_orders=True
    )
    assert result is not None
    status, _msg = result
    assert status == 403


def test_build_user_delete_blocker_blocks_self_delete(db_session):
    actor = _FakeUser(7, "editor@zozi.com")
    result = build_user_delete_blocker._build_user_delete_blocker(
        actor, {"id": 7}, db_session, delete_orders=True
    )
    assert result is not None
    status, _msg = result
    assert status == 403


def test_build_user_delete_blocker_allows_delete(db_session):
    target = _FakeUser(8, "target@zozi.com")
    assert build_user_delete_blocker._build_user_delete_blocker(
        target, {"id": 2}, db_session, delete_orders=True
    ) is None


def test_create_update_and_reset_staff_user(db_session):
    user = ops.create_staff_user(
        db_session,
        email="staff_recovered@zozi.com",
        hashed_password="old-hash",
        role="staff",
    )
    assert user.id is not None

    ops.update_staff_user(db_session, user, {"full_name": "Recovered Staff"})
    db_session.refresh(user)
    assert user.full_name == "Recovered Staff"

    ops.force_reset_password(db_session, user, "new-hash")
    db_session.refresh(user)
    assert user.hashed_password == "new-hash"


def test_create_chatbot_query_event(db_session):
    event = ops.create_chatbot_query_event(
        db_session,
        session_id="sess-1",
        event_type="search",
        user_id=None,
        message="find shoes",
        result_count=3,
    )
    assert event.id is not None
    assert event.session_id == "sess-1"
    assert event.result_count == 3


def test_update_user_browsing_history(db_session):
    user = ops.create_staff_user(
        db_session,
        email="browse_recovered@zozi.com",
        hashed_password="h",
        role="customer",
    )
    ops.update_user_browsing_history(db_session, user, 42)
    ops.update_user_browsing_history(db_session, user, 99)
    db_session.refresh(user)
    # Most-recent first, capped (no error), de-duplicated.
    assert user.browsing_history_json is not None
    assert user.browsing_history_json.startswith("[") and "99" in user.browsing_history_json
    assert "42" in user.browsing_history_json
