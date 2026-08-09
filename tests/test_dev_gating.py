"""Tests that DBA02 schema-bootstrap helpers are dev-gated (never run in production).

Mirrors the audit rule: ``Base.metadata.create_all`` must be gated behind a
non-production environment so it can never touch a real production database.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

# Make the backend package importable (mirrors backend/tests/conftest.py).
_BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import pytest  # noqa: E402

import db.init_db as init_db  # noqa: E402


def _stub_settings(monkeypatch, app_env: str) -> None:
    monkeypatch.setattr(init_db, "settings", types.SimpleNamespace(app_env=app_env))


def _spy_create_all(monkeypatch) -> list:
    calls: list = []
    monkeypatch.setattr(
        init_db.Base.metadata, "create_all", lambda bind: calls.append(bind)
    )
    return calls


def test_create_tables_refuses_production(monkeypatch):
    _stub_settings(monkeypatch, "production")
    calls = _spy_create_all(monkeypatch)
    with pytest.raises(RuntimeError):
        init_db._create_tables()
    assert calls == []


def test_create_tables_allowed_in_development(monkeypatch):
    _stub_settings(monkeypatch, "development")
    calls = _spy_create_all(monkeypatch)
    init_db._create_tables()
    assert len(calls) == 1
