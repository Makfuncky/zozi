"""Architecture gate: B6 / R6 — keyset (cursor) pagination on hot lists.

ARCHITECTURE_DIAGRAM.md §6 mandates "Keyset pagination (cursor), NEVER OFFSET on
hot lists". This test enforces that the orders hot-list reader uses keyset
pagination (offset-free) and that the keyset cursor machinery is correct and
tamper-evident.
"""
from __future__ import annotations

import ast
import glob
import os

import pytest
from sqlalchemy import Column, DateTime, Integer, MetaData, Table, create_engine
from sqlalchemy.orm import Session

from infrastructure.utils.pagination import (
    decode_keyset_cursor,
    encode_keyset_cursor,
    get_max_page_size,
    keyset_offset_window,
    keyset_paginate,
)


def _make_table():
    meta = MetaData()
    t = Table(
        "orders",
        meta,
        Column("id", Integer, primary_key=True),
        Column("created_at", DateTime),
    )
    return t


def _seed(session, table, n=25):
    from datetime import datetime, timedelta

    rows = []
    for i in range(n):
        # created_at strictly increasing with id so DESC order is unambiguous
        rows.append({"id": i + 1, "created_at": datetime(2024, 1, 1) + timedelta(minutes=i)})
    session.execute(table.insert(), rows)
    session.commit()


def test_keyset_pagination_exposed():
    """The diagram's mandated mechanism exists."""
    assert callable(keyset_paginate)
    assert callable(encode_keyset_cursor)
    assert callable(decode_keyset_cursor)


def test_cursor_roundtrip_and_tamper_rejection():
    values = ["2024-01-01T00:05:00", 7]
    cursor = encode_keyset_cursor(values, secret="test-secret")
    assert "." in cursor  # signature appended
    decoded = decode_keyset_cursor(cursor, secret="test-secret")
    assert decoded == values

    # tampered payload must be rejected
    payload, _, sig = cursor.rpartition(".")
    tampered = f"{payload[:-2]}.{sig}"
    assert decode_keyset_cursor(tampered, secret="test-secret") is None

    # wrong secret must be rejected
    assert decode_keyset_cursor(cursor, secret="other-secret") is None

    # empty cursor -> None
    assert decode_keyset_cursor(None) is None
    assert decode_keyset_cursor("") is None


def test_keyset_paginate_covers_dataset_without_offset():
    """Keyset paging returns every row exactly once, ordered, with no OFFSET."""
    engine = create_engine("sqlite:///:memory:")
    table = _make_table()
    table.metadata.create_all(engine)
    session = Session(engine)
    _seed(session, table, n=25)

    query = session.query(table.c.id, table.c.created_at)
    sort_keys = [(table.c.created_at, "desc"), (table.c.id, "desc")]

    # patch Query.offset to prove keyset_paginate never uses OFFSET
    calls = []
    original_offset = type(query).offset

    def spy_offset(self, *a, **k):
        calls.append(1)
        return original_offset(self, *a, **k)

    type(query).offset = spy_offset
    try:
        page1 = keyset_paginate(query, sort_keys=sort_keys, page_size=10)
        assert len(page1["items"]) == 10
        assert page1["has_next"] is True
        assert page1["next_cursor"] is not None

        page2 = keyset_paginate(
            query, sort_keys=sort_keys, cursor=page1["next_cursor"], page_size=10
        )
        assert len(page2["items"]) == 10
        assert page2["has_next"] is True  # 25 rows -> a 3rd page exists

        page3 = keyset_paginate(
            query, sort_keys=sort_keys, cursor=page2["next_cursor"], page_size=10
        )
        assert len(page3["items"]) == 5
        assert page3["has_next"] is False
    finally:
        type(query).offset = original_offset

    # No OFFSET was ever issued by the keyset path
    assert calls == [], "keyset_paginate must not call Query.offset()"

    ids1 = [r[0] for r in page1["items"]]
    ids2 = [r[0] for r in page2["items"]]
    ids3 = [r[0] for r in page3["items"]]
    # pages are strictly descending and non-overlapping
    assert ids1 == sorted(ids1, reverse=True)
    assert ids2 == sorted(ids2, reverse=True)
    assert ids3 == sorted(ids3, reverse=True)
    assert set(ids1) | set(ids2) | set(ids3) == set(range(1, 26))
    assert not (set(ids1) & set(ids2) & set(ids3))


def test_orders_hot_list_is_keyset_not_offset():
    """B6 / R6 enforcement: the canonical orders hot-list reader is offset-free."""
    import inspect

    from domains.orders import ports

    src = inspect.getsource(ports.list_orders_keyset)
    assert ".offset(" not in src, "list_orders_keyset must use keyset pagination, not OFFSET"
    assert "keyset_paginate" in src, "list_orders_keyset must delegate to keyset_paginate"


def test_catalog_hot_list_is_keyset_not_offset():
    """B6 / R6 enforcement extends to the catalog products hot list.

    Products are the busiest read surface in a marketplace, so the canonical
    ``list_products_keyset`` reader must also be offset-free and delegate to
    ``keyset_paginate`` (the same 100Ks-scale strategy as orders).
    """
    import inspect

    from domains.catalog import ports

    src = inspect.getsource(ports.list_products_keyset)
    assert ".offset(" not in src, "list_products_keyset must use keyset pagination, not OFFSET"
    assert "keyset_paginate" in src, "list_products_keyset must delegate to keyset_paginate"


def test_users_hot_list_is_keyset_not_offset():
    """B6 / R6 enforcement extends to the admin users hot list.

    The canonical ``list_users_keyset`` reader must be offset-free and delegate
    to ``keyset_paginate`` (the same 100Ks-scale strategy as orders/catalog).
    """
    import inspect

    from domains.governance.services import users_service

    src = inspect.getsource(users_service.list_users_keyset)
    assert ".offset(" not in src, "list_users_keyset must use keyset pagination, not OFFSET"
    assert "keyset_paginate" in src, "list_users_keyset must delegate to keyset_paginate"


def test_keyset_offset_window_avoids_offset_and_matches():
    """``keyset_offset_window`` returns the same window as OFFSET, but never OFFSETs.

    This is the migration primitive for the adoption-layer list endpoints: they
    keep their ``offset``/``limit`` API, but the window is reached by walking
    keyset cursors (B6 / R6 — never OFFSET on hot lists).
    """
    engine = create_engine("sqlite:///:memory:")
    table = _make_table()
    table.metadata.create_all(engine)
    session = Session(engine)
    _seed(session, table, n=25)

    query = session.query(table.c.id, table.c.created_at)
    sort_keys = [(table.c.created_at, "desc"), (table.c.id, "desc")]

    # spy to prove keyset_offset_window never issues OFFSET
    calls = []
    original_offset = type(query).offset

    def spy_offset(self, *a, **k):
        calls.append(1)
        return original_offset(self, *a, **k)

    type(query).offset = spy_offset
    try:
        full_ids = list(range(25, 0, -1))  # strictly descending by created_at/id
        cases = [(0, 10), (10, 10), (20, 10), (3, 7), (24, 5), (0, 100)]
        for off, lim in cases:
            got = keyset_offset_window(query, sort_keys=sort_keys, offset=off, limit=lim)
            got_ids = [r[0] for r in got]
            expected = full_ids[off:off + lim]
            assert got_ids == expected, f"offset={off} limit={lim}: {got_ids} != {expected}"
    finally:
        type(query).offset = original_offset

    assert calls == [], "keyset_offset_window must not call Query.offset()"


def test_keyset_offset_window_joined_tuple_matches():
    """``keyset_offset_window`` works on joined ``(entity, scalar)`` tuple rows.

    Mirrors the bank-account verification lists: ``query(Model, Other.col)``
    returns heterogeneous tuples, so the cursor must extract the sort value from
    the owning entity inside the tuple — never from a bare ``getattr(row, name)``.
    The window must equal the OFFSET equivalent and must never issue OFFSET.
    """
    from datetime import datetime, timedelta

    from sqlalchemy import ForeignKey, String
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()

    class _Par(Base):
        __tablename__ = "ko_parent"
        id = Column(Integer, primary_key=True)
        created_at = Column(DateTime)

    class _Chd(Base):
        __tablename__ = "ko_child"
        id = Column(Integer, primary_key=True)
        parent_id = Column(Integer, ForeignKey("ko_parent.id"))
        label = Column(String)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    session.add_all(
        [_Par(id=i + 1, created_at=datetime(2024, 1, 1) + timedelta(minutes=i)) for i in range(25)]
    )
    session.commit()
    session.add_all(
        [_Chd(id=i + 1, parent_id=i + 1, label=f"c{i + 1}") for i in range(25)]
    )
    session.commit()

    query = session.query(_Par, _Chd.label).join(_Chd, _Chd.parent_id == _Par.id)
    sort_keys = [(_Par.created_at, "desc"), (_Par.id, "desc")]

    calls = []
    original_offset = type(query).offset

    def spy_offset(self, *a, **k):
        calls.append(1)
        return original_offset(self, *a, **k)

    type(query).offset = spy_offset
    try:
        full_ids = list(range(25, 0, -1))
        cases = [(0, 10), (10, 10), (20, 10), (3, 7), (0, 100)]
        for off, lim in cases:
            got = keyset_offset_window(query, sort_keys=sort_keys, offset=off, limit=lim)
            got_ids = [r[0].id for r in got]
            expected = full_ids[off:off + lim]
            assert got_ids == expected, f"offset={off} limit={lim}: {got_ids} != {expected}"
    finally:
        type(query).offset = original_offset

    assert calls == [], "keyset_offset_window must not call Query.offset() on joined queries"


def test_keyset_offset_window_scalar_tuple_matches():
    """``keyset_offset_window`` works on scalar-only ``(col1, col2)`` tuples.

    Many list endpoints do ``query(Model.id, Model.name)`` and never carry the
    entity object. The cursor must locate the sort column by its select position
    (via ``column_descriptions``), never by attribute access. The window must
    equal the OFFSET equivalent and must never issue OFFSET.
    """
    engine = create_engine("sqlite:///:memory:")
    table = _make_table()
    table.metadata.create_all(engine)
    session = Session(engine)
    _seed(session, table, n=25)

    query = session.query(table.c.id, table.c.created_at)
    sort_keys = [(table.c.created_at, "desc"), (table.c.id, "desc")]

    calls = []
    original_offset = type(query).offset

    def spy_offset(self, *a, **k):
        calls.append(1)
        return original_offset(self, *a, **k)

    type(query).offset = spy_offset
    try:
        full_ids = list(range(25, 0, -1))
        cases = [(0, 10), (10, 10), (20, 10), (3, 7), (0, 100)]
        for off, lim in cases:
            got = keyset_offset_window(query, sort_keys=sort_keys, offset=off, limit=lim)
            got_ids = [r[0] for r in got]
            expected = full_ids[off:off + lim]
            assert got_ids == expected, f"offset={off} limit={lim}: {got_ids} != {expected}"
    finally:
        type(query).offset = original_offset

    assert calls == [], "keyset_offset_window must not call Query.offset() on scalar-tuple queries"


def test_get_all_users_is_keyset_not_offset():
    """Adoption-layer ``get_all_users`` off SQL OFFSET via keyset_offset_window."""
    import inspect

    from domains.governance.services import users_service

    src = inspect.getsource(users_service.get_all_users)
    assert ".offset(" not in src, "get_all_users must use keyset pagination, not OFFSET"
    assert "keyset_offset_window" in src, "get_all_users must delegate to keyset_offset_window"


def test_pending_bank_accounts_is_keyset_not_offset():
    """Adoption-layer bank-account lists off SQL OFFSET via keyset_offset_window."""
    import inspect

    from domains.governance.services import users_service

    src = inspect.getsource(users_service.list_pending_bank_accounts)
    assert ".offset(" not in src, "list_pending_bank_accounts must use keyset pagination, not OFFSET"
    assert "keyset_offset_window" in src, "list_pending_bank_accounts must delegate to keyset_offset_window"


def test_users_basic_is_keyset_not_offset():
    """B6 / R6 enforcement: an adoption-layer list migrated to keyset_offset_window.

    ``list_users_basic`` is the first adoption-layer function ported off SQL
    OFFSET using the reusable ``keyset_offset_window`` primitive — it keeps its
    ``skip``/``limit`` window but no longer issues OFFSET.
    """
    import inspect

    from domains.governance.services import users_service

    src = inspect.getsource(users_service.list_users_basic)
    assert ".offset(" not in src, "list_users_basic must use keyset pagination, not OFFSET"
    assert "keyset_offset_window" in src, "list_users_basic must delegate to keyset_offset_window"


def test_products_admin_list_is_keyset_not_offset():
    """B6 / R6 adoption: admin product list off SQL OFFSET via keyset_offset_window."""
    import inspect

    from domains.governance.services import products_service

    src = inspect.getsource(products_service.get_all_products)
    assert ".offset(" not in src, "get_all_products must use keyset pagination, not OFFSET"
    assert "keyset_offset_window" in src, "get_all_products must delegate to keyset_offset_window"


def test_all_domain_ports_are_offset_free():
    """B6 / R6 enforcement scales to EVERY domain's sanctioned read surface.

    The diagram mandates "NEVER OFFSET on hot lists". The sanctioned cross-domain
    read surface is ``domains/<name>/ports.py``. Every paginated hot-list reader
    there (``list_*_page`` / ``list_*_keyset``) must be offset-free and delegate to
    a keyset helper. This locks in orders, catalog, finance, customers and
    suppliers so no regression to OFFSET can land in the read surface — without
    fabricating redundant readers where the surface is already keyset-clean or
    empty (customers/suppliers publish no models via ports yet).

    NB: the ~100+ remaining OFFSET calls in ``domains/*/services`` and routers are
    the *adoption* layer and stay deferred per PART 0.7 (frontend cursor
    coordination); this gate protects the read surface they must eventually call.
    """
    # keyset helpers that are guaranteed offset-free
    KEYSET_CALLS = (
        "keyset_paginate(",
        "cursor_paginate_asc(",
        "_keyset_page(",
        "_keyset_list(",
        "keyset_paginated_response(",
    )

    here = os.path.dirname(os.path.abspath(__file__))
    domains_dir = os.path.abspath(os.path.join(here, "..", "..", "domains"))
    ports_files = sorted(glob.glob(os.path.join(domains_dir, "*", "ports.py")))
    assert ports_files, "expected domain ports.py files"

    for ports_path in ports_files:
        with open(ports_path, "r", encoding="utf-8") as fh:
            module_src = fh.read()

        # the whole sanctioned read surface must never use OFFSET
        assert ".offset(" not in module_src, (
            f"{os.path.basename(os.path.dirname(ports_path))}/ports.py "
            f"must not use OFFSET pagination (B6/R6)"
        )

        # every paginated hot-list reader must delegate to a keyset helper
        tree = ast.parse(module_src)
        lines = module_src.splitlines()
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name.startswith("list_")
                and ("_page" in node.name or "_keyset" in node.name)
            ):
                fn_src = "\n".join(lines[node.lineno - 1 : node.end_lineno])
                assert ".offset(" not in fn_src, (
                    f"{node.name} in {ports_path} must use keyset pagination, "
                    f"not OFFSET"
                )
                assert any(call in fn_src for call in KEYSET_CALLS), (
                    f"{node.name} in {ports_path} must delegate to a keyset helper"
                )


def test_keyset_paginated_response_shape_and_compat():
    """The backward-compatible keyset envelope keeps legacy fields for clients."""
    from infrastructure.utils.pagination import keyset_paginated_response

    engine = create_engine("sqlite:///:memory:")
    table = _make_table()
    table.metadata.create_all(engine)
    session = Session(engine)
    _seed(session, table, n=25)

    query = session.query(table.c.id, table.c.created_at)
    sort_keys = [(table.c.created_at, "desc"), (table.c.id, "desc")]

    page1 = keyset_paginated_response(
        query, sort_keys=sort_keys, page_size=10, total=25
    )
    assert set(page1.keys()) >= {
        "items", "next_cursor", "page_size", "has_next", "total", "page", "pages"
    }
    assert len(page1["items"]) == 10
    assert page1["has_next"] is True
    assert page1["next_cursor"] is not None
    assert page1["total"] == 25
    assert page1["page"] is None
    assert page1["pages"] == 3  # ceil(25 / 10)

    page2 = keyset_paginated_response(
        query, sort_keys=sort_keys, cursor=page1["next_cursor"], page_size=10
    )
    # legacy fields omitted when no total supplied
    assert page2["total"] is None
    assert page2["pages"] is None
    assert len(page2["items"]) == 10


def test_page_size_caps_from_env(monkeypatch):
    monkeypatch.setenv("MAX_PAGE_SIZE", "25")
    assert get_max_page_size() == 25


def test_supplier_documents_is_keyset_not_offset():
    """B6 / R6 adoption: supplier document lists off SQL OFFSET via keyset_offset_window.

    ``list_my_documents`` and the admin document list both paginate
    ``SupplierDocument``. They keep their ``offset``/``limit`` window but no longer
    issue SQL OFFSET — the 100Ks-scale seek path is used instead.
    """
    import inspect

    from domains.suppliers.services import supplier_kyc_service

    for fn in (
        supplier_kyc_service.list_my_documents,
        supplier_kyc_service.list_supplier_documents,
    ):
        src = inspect.getsource(fn)
        assert ".offset(" not in src, f"{fn.__name__} must use keyset pagination, not OFFSET"
        assert "keyset_offset_window" in src, f"{fn.__name__} must delegate to keyset_offset_window"


def test_supplier_products_is_keyset_not_offset():
    """B6 / R6 adoption: supplier product list off SQL OFFSET via keyset_offset_window."""
    import inspect

    from domains.suppliers.services import supplier_service

    src = inspect.getsource(supplier_service.get_supplier_products)
    assert ".offset(" not in src, "get_supplier_products must use keyset pagination, not OFFSET"
    assert "keyset_offset_window" in src, "get_supplier_products must delegate to keyset_offset_window"
