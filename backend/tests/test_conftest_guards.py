"""Guard tests for the test-database setup.

These tests assert invariants that prevent the "unable to open database file"
and "unknown database catalog" failures from recurring.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import tests.conftest as _conftest
from infrastructure.database.base import Base


class TestTestDbPath:
    """The global test-DB path must be absolute and unique per xdist worker."""

    def test_path_is_absolute(self):
        assert os.path.isabs(_conftest._test_db_path), (
            f"_test_db_path must be absolute, got {_conftest._test_db_path!r}"
        )

    def test_path_is_unique_per_worker(self):
        worker = os.environ.get("PYTEST_XDIST_WORKER")
        if worker:
            assert f"test_{worker}.db" in _conftest._test_db_path, (
                f"Per-worker path should contain worker id, got {_conftest._test_db_path!r}"
            )

    def test_parent_directory_exists(self):
        parent = os.path.dirname(_conftest._test_db_path)
        assert os.path.isdir(parent), (
            f"Parent directory of test DB must exist, got {parent!r}"
        )


class TestSchemaTranslateMap:
    """schema_translate_map must cover every schema declared by an ORM model."""

    def test_all_declared_schemas_are_in_map(self):
        declared = {t.schema for t in Base.metadata.tables.values() if t.schema}
        mapped = set(_conftest.SCHEMA_TRANSLATE_MAP.keys())
        missing = declared - mapped
        assert not missing, (
            f"SCHEMA_TRANSLATE_MAP is missing schemas: {sorted(missing)}. "
            f"Declared: {sorted(declared)}, Mapped: {sorted(mapped)}"
        )

    def test_conftest_monkeypatch_injects_map_for_test_engines(self):
        """A SQLite engine created without schema_translate_map should receive one."""
        test_url = "sqlite:///:memory:"
        eng = create_engine(test_url, connect_args={"check_same_thread": False})
        try:
            opts = eng.get_execution_options()
            assert "schema_translate_map" in opts, (
                "create_engine monkeypatch did not inject schema_translate_map"
            )
            stm = opts["schema_translate_map"]
            declared = {t.schema for t in Base.metadata.tables.values() if t.schema}
            for schema in declared:
                assert schema in stm, f"schema_translate_map missing {schema!r}"
        finally:
            eng.dispose()


class TestNoMagicMockFixtures:
    """No fixture in conftest may return a bare MagicMock for a critical object."""

    def test_engine_fixture_returns_real_engine(self, engine):
        assert not isinstance(engine, MagicMock), (
            "engine fixture must not return MagicMock; got a bare mock"
        )
        from sqlalchemy.engine import Engine
        assert isinstance(engine, Engine), (
            f"engine fixture must return a real SQLAlchemy Engine, got {type(engine).__name__}"
        )

    def test_db_session_fixture_returns_real_session(self, db_session):
        assert not isinstance(db_session, MagicMock), (
            "db_session fixture must not return MagicMock; got a bare mock"
        )
        assert isinstance(db_session, Session), (
            f"db_session fixture must return a real Session, got {type(db_session).__name__}"
        )

    def test_app_fixture_returns_real_app(self, app):
        assert not isinstance(app, MagicMock), (
            "app fixture must not return MagicMock; got a bare mock"
        )
        from fastapi import FastAPI
        assert isinstance(app, FastAPI), (
            f"app fixture must return a real FastAPI app, got {type(app).__name__}"
        )

    def test_client_fixture_returns_real_client(self, client):
        assert not isinstance(client, MagicMock), (
            "client fixture must not return MagicMock; got a bare mock"
        )
        from fastapi.testclient import TestClient
        assert isinstance(client, TestClient), (
            f"client fixture must return a real TestClient, got {type(client).__name__}"
        )
