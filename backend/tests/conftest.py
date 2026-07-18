"""Shared pytest fixtures for the Zozi backend test-suite.

The recovered codebase had no ``tests/conftest.py`` (it was absent from the
codebase dumps). This provides the minimal harness needed to boot the app under
pytest with an isolated SQLite database and a FastAPI ``TestClient``.

Usage in a test module::

    from fastapi.testclient import TestClient

    def test_health(client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200

These fixtures intentionally avoid importing ``main`` at collection time (the
app eagerly loads every router); ``app`` / ``client`` import lazily so that
``pytest --co`` stays fast and resilient to unrelated router failures.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Ensure the backend package root is importable regardless of cwd.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(_BACKEND_ROOT))

from db.base import Base  # noqa: E402


@pytest.fixture(scope="session")
def db_file() -> Iterator[str]:
    """Create a throwaway SQLite file for the test session."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="zozi_test_")
    os.close(fd)
    yield path
    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture(scope="session")
def engine(db_file: str):
    eng = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        poolclass=__import__("sqlalchemy.pool", fromlist=["StaticPool"]).StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture
def db_session(engine) -> Iterator[Session]:
    """Yield a session bound to the test engine, rolled back after each test."""
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def app(engine):
    """Build the FastAPI app with the DB dependency overridden to the test engine."""
    from db.database import SessionLocal as _RealSessionLocal  # noqa: F401
    from fastapi.testclient import TestClient  # noqa: F401

    import main as _main  # noqa: F401  (ensures routers are importable)

    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def _override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    _main.app.dependency_overrides[_main.get_db] = _override_get_db
    yield _main.app
    _main.app.dependency_overrides.clear()


@pytest.fixture
def client(app) -> Iterator["TestClient"]:  # type: ignore[name-defined]
    """A FastAPI TestClient wired to the test database."""
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c
