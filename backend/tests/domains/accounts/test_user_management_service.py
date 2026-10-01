"""Paired test for FILE-46: get_user_role explicit error handling (AP-26).

Law: explicit error handling instead of silent "unknown" fallback.
"""
from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from domains.accounts.services.users.user_management_service import (
    get_user_role,
    _get_role_features,
    _default_permissions_for_role,
    update_user_role,
)


class FakeUser:
    def __init__(self, id: int, role: str | None = None):
        self.id = id
        self.role = role


class FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._result


class FakeSession:
    def __init__(self, user_result=None):
        self._user_result = user_result

    def query(self, model):
        return FakeQuery(self._user_result)


def test_get_user_role_raises_when_user_not_found():
    db = FakeSession(user_result=None)
    with pytest.raises(ValueError, match="User 1 not found"):
        get_user_role(db, 1)


def test_get_user_role_raises_when_role_is_none():
    db = FakeSession(user_result=FakeUser(id=1, role=None))
    with pytest.raises(ValueError, match="User 1 has no role"):
        get_user_role(db, 1)


def test_get_user_role_raises_when_role_is_empty_string():
    db = FakeSession(user_result=FakeUser(id=1, role=""))
    with pytest.raises(ValueError, match="User 1 has no role"):
        get_user_role(db, 1)


def test_get_user_role_returns_role_when_set():
    db = FakeSession(user_result=FakeUser(id=1, role="admin"))
    assert get_user_role(db, 1) == "admin"


def test_no_unknown_fallback_in_source():
    from pathlib import Path
    src = Path(__file__).resolve().parent.parent.parent.parent / "domains" / "accounts" / "services" / "users" / "user_management_service.py"
    content = src.read_text(encoding="utf-8")
    assert '"unknown"' not in content


def test_get_role_features_returns_empty_without_injection():
    assert _get_role_features() == {}


def test_get_role_features_returns_injected_mapping():
    mapping = {"admin": ["users.read", "users.role.update"]}
    assert _get_role_features(role_features=mapping) == mapping


def test_default_permissions_for_role_returns_empty_without_injection():
    assert _default_permissions_for_role("admin") == []


def test_default_permissions_for_role_uses_injected_mapping():
    mapping = {"admin": ["users.read", "users.role.update"]}
    assert _default_permissions_for_role("admin", role_features=mapping) == ["users.read", "users.role.update"]


def test_update_user_role_raises_app_error_for_invalid_role():
    db = FakeSession(user_result=None)
    with pytest.raises(Exception) as exc_info:
        update_user_role(1, "invalid_role", {"id": 1, "role": "admin"}, db)
    assert exc_info.type.__name__ == "AppError"
    assert exc_info.value.status_code == 400


def test_no_fastapi_http_exception_import_in_source():
    from pathlib import Path
    src = Path(__file__).resolve().parent.parent.parent.parent / "domains" / "accounts" / "services" / "users" / "user_management_service.py"
    content = src.read_text(encoding="utf-8")
    assert "from fastapi import HTTPException" not in content
    assert "from rbac.dependencies import _ROLE_FEATURES" not in content

