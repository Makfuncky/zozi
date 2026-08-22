"""Functional check for comms/finance/governance/hr/logistics/media/payments
ports keyset (cursor) pagination wiring.

Mirrors ``tests/test_accounts_keyset_pagination.py``. Uses a generic minimal
model (id primary key) on an in-memory SQLite engine to prove the ``_keyset_list``
and ``_keyset_page`` helpers — which every domain ``ports.py`` now routes its hot
``list_*`` through — paginate correctly with cursors and a stable ``id`` order
(NO OFFSET on hot lists, per diagram §6). The domain models use Postgres-only
column types and cannot be created on SQLite, so the generic helpers are
validated with an equivalent schema instead.
"""

from __future__ import annotations

import inspect

from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.orm import Session, declarative_base

from infrastructure.utils.pagination import CursorPage

from domains.comms import ports as comms_ports
from domains.finance import ports as finance_ports
from domains.governance import ports as governance_ports
from domains.hr import ports as hr_ports
from domains.logistics import ports as logistics_ports
from domains.media import ports as media_ports
from domains.payments import ports as payments_ports

Base = declarative_base()

_Row = type("_Row", (Base,), {
    "__tablename__": "ks_row",
    "id": Column(Integer, primary_key=True),
})

# (module, plain list fn, page companion fn) — one representative per domain.
REPS = [
    (comms_ports, "list_notifications", "list_notifications_page"),
    (finance_ports, "list_invoices", "list_invoices_page"),
    (governance_ports, "list_system_alerts", "list_system_alerts_page"),
    (hr_ports, "list_employees", "list_employees_page"),
    (logistics_ports, "list_shipments", "list_shipments_page"),
    (media_ports, "list_media_assets", "list_media_assets_page"),
    (payments_ports, "list_payments", "list_payments_page"),
]


def _seed(n: int = 25):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = Session(engine)
    for _ in range(n):
        db.add(_Row())
    db.commit()
    return engine, db


def _routes_through(func, helper_name: str) -> bool:
    """True if ``func``'s source calls the named keyset helper (regression guard)."""
    return helper_name in inspect.getsource(func)


def test_keyset_list_plain_returns_ordered_list():
    engine, db = _seed()
    try:
        rows = comms_ports._keyset_list(_Row, db, limit=10)
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
            page: CursorPage = comms_ports._keyset_page(_Row, db, cursor=cursor, page_size=10)
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


def test_all_domains_list_and_page_companions_wired_to_keyset():
    # The public ``list_*`` keeps its List contract (backward compatible) and must
    # now be sourced via ``_keyset_list``; the scale-ready ``*_page`` companions
    # must return a ``CursorPage`` via ``_keyset_page``.
    for module, list_fn, page_fn in REPS:
        assert _routes_through(getattr(module, list_fn), "_keyset_list")
        assert _routes_through(getattr(module, page_fn), "_keyset_page")
