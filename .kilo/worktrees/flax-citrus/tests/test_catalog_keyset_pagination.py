"""Functional check for catalog ports keyset (cursor) pagination wiring.

Uses a generic minimal model (same column shape as catalog models: id / created_at /
country_code / is_deleted) on an in-memory SQLite engine to prove the ``_keyset_list``
and ``_keyset_page`` helpers — which ``domains.catalog.ports`` now routes every hot
``list_*`` through — paginate correctly with cursors, country scoping, and soft-delete.
The catalog ``Product``/``Category``/``Review`` models use Postgres-only column types
and cannot be created on SQLite, so the generic helpers are validated with an
equivalent schema instead.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base

from infrastructure.utils.pagination import CursorPage

from domains.catalog import ports

Base = declarative_base()


class _Row(Base):
    __tablename__ = "ks_test_row"
    id = __import__("sqlalchemy").Column(Integer, primary_key=True)
    created_at = __import__("sqlalchemy").Column(DateTime, default=lambda: datetime.now(timezone.utc))
    country_code = __import__("sqlalchemy").Column(String(8), default="OM")
    is_deleted = __import__("sqlalchemy").Column(Boolean, default=False)


def _seed(n: int = 25):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = Session(engine)
    for i in range(n):
        db.add(_Row(country_code="OM" if i % 2 == 0 else "AE", is_deleted=(i % 7 == 0)))
    db.commit()
    return engine, db


def test_keyset_list_plain_returns_ordered_list():
    engine, db = _seed()
    try:
        rows = ports._keyset_list(_Row, db, limit=10)
        assert isinstance(rows, list)
        assert len(rows) == 10
        ids = [r.id for r in rows]
        assert ids == sorted(ids)  # stable id ordering, no OFFSET used
    finally:
        db.close()
        engine.dispose()


def test_keyset_page_cursor_iterates_without_overlap():
    engine, db = _seed(25)
    try:
        collected = []
        cursor = None
        pages = 0
        while True:
            page: CursorPage = ports._keyset_page(_Row, db, cursor=cursor, page_size=10)
            assert isinstance(page, CursorPage)
            collected.extend(page.items)
            pages += 1
            if not page.next_cursor:
                break
            cursor = page.next_cursor
        assert len(collected) == 25
        ids = [r.id for r in collected]
        assert ids == sorted(ids)  # monotonic, no duplicates
        assert pages == 3  # 10 + 10 + 5
    finally:
        db.close()
        engine.dispose()


def test_keyset_page_country_scope_and_soft_delete():
    engine, db = _seed(25)
    try:
        # Only OM, exclude soft-deleted (has_deleted=True enables the is_deleted filter)
        page = ports._keyset_page(_Row, db, page_size=100, country_code="OM", include_deleted=False, has_deleted=True)
        assert all(r.country_code == "OM" for r in page.items)
        assert all(not r.is_deleted for r in page.items)
        # OM including soft-deleted has more rows than OM excluding
        page_all = ports._keyset_page(_Row, db, page_size=100, country_code="OM", include_deleted=True, has_deleted=True)
        assert len(page_all.items) >= len(page.items)
    finally:
        db.close()
        engine.dispose()
