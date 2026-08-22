"""Functional check for accounts ports keyset (cursor) pagination wiring.

Uses a generic minimal model (id primary key, same column shape the accounts
models use) on an in-memory SQLite engine to prove the ``_keyset_list`` and
``_keyset_page`` helpers — which ``domains.accounts.ports`` now routes every hot
``list_*`` through — paginate correctly with cursors and a stable ``id`` order
(NO OFFSET on hot lists, per diagram §6). The Account models use Postgres-only
column types and cannot be created on SQLite, so the generic helpers are
validated with an equivalent schema instead.
"""

from __future__ import annotations

from sqlalchemy import Integer, create_engine
from sqlalchemy.orm import Session, declarative_base

from infrastructure.utils.pagination import CursorPage

from domains.accounts import ports

Base = declarative_base()


class _Row(Base):
    __tablename__ = "ks_acc_row"
    id = __import__("sqlalchemy").Column(Integer, primary_key=True)


def _seed(n: int = 25):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = Session(engine)
    for _ in range(n):
        db.add(_Row())
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


import inspect


def _routes_through(func, helper_name: str) -> bool:
    """True if ``func``'s source calls the named keyset helper (regression guard)."""
    return helper_name in inspect.getsource(func)


def test_accounts_list_and_page_companions_are_wired_to_keyset():
    # The public ``list_*`` keeps its List contract (backward compatible) and must
    # now be sourced via ``_keyset_list``; the scale-ready ``*_page`` companions
    # must return a ``CursorPage`` via ``_keyset_page``.
    assert _routes_through(ports.list_users, "_keyset_list")
    assert _routes_through(ports.list_users_page, "_keyset_page")
    assert _routes_through(ports.list_addresss, "_keyset_list")
    assert _routes_through(ports.list_addresss_page, "_keyset_page")
    assert _routes_through(ports.list_revoked_tokens, "_keyset_list")
    assert _routes_through(ports.list_revoked_tokens_page, "_keyset_page")
