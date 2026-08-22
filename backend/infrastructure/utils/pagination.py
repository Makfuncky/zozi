"""Safe pagination helpers for list endpoints.

Enforces hard caps so an unbounded query never OOMs the server.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Iterator, Optional, Sequence

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Query

# Hard cap on page size — any request above this is silently clamped.
MAX_PAGE_SIZE = 100
MAX_EXPORT_SIZE = 5000

# Absolute hard limit for any single query to prevent OOM.
SAFE_QUERY_LIMIT = 1000


def _get_max_page_size_from_env() -> int:
    val = os.environ.get("MAX_PAGE_SIZE")
    if val is not None:
        try:
            return max(1, int(val))
        except (ValueError, TypeError):
            pass
    return MAX_PAGE_SIZE


def safe_page(page: Optional[int], size: Optional[int], max_size: int = MAX_PAGE_SIZE) -> tuple[int, int]:
    """Return a (page, size) tuple clamped to safe bounds."""
    page = max(1, page or 1)
    size = min(max_size, max(1, size or 20))
    return page, size


def paginated_query(
    query: Query,
    page: int = 1,
    size: int = 20,
    max_size: int = MAX_PAGE_SIZE,
) -> tuple[Sequence[Any], int]:
    """Execute a paginated query and return ``(items, total_count)``.

    The total count is computed from the *unmodified* query (before offset/limit)
    so it reflects the full result set.
    """
    page, size = safe_page(page, size, max_size)
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return items, total


def paginated_response(
    query: Query,
    page: int = 1,
    size: int = 20,
    max_size: int = MAX_PAGE_SIZE,
    serializer: Optional[Callable[[Any], dict]] = None,
) -> dict:
    """Return a standard pagination envelope for list endpoints.

    Example response::

        {
            "items": [...],
            "total": 142,
            "page": 1,
            "size": 20,
            "pages": 8,
        }
    """
    page, size = safe_page(page, size, max_size)
    total = query.count()
    pages = max(1, (total + size - 1) // size)
    items = query.offset((page - 1) * size).limit(size).all()

    if serializer:
        items = [serializer(item) for item in items]

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }


def windowed_iterate(query: Query, window_size: int = SAFE_QUERY_LIMIT) -> Iterator[Any]:
    """Yield every row from ``query`` in bounded windows to cap memory use.

    The query is expected to already specify its ORDER BY (and may carry an
    optional ``.limit(n)`` that acts as a total cap). Windowing uses offset/limit
    pagination so a very large result set never loads fully into memory.

    Each call is generative — the caller's ``query`` object is not mutated.
    """
    total_cap = getattr(query, "_limit", None)
    remaining = int(total_cap) if total_cap is not None else None
    offset = 0
    while True:
        if remaining is not None and remaining <= 0:
            return
        size = window_size if remaining is None else min(window_size, remaining)
        window = query.offset(offset).limit(size).all()
        if not window:
            return
        for row in window:
            yield row
        n = len(window)
        if remaining is not None:
            remaining -= n
        offset += n
        if n < size:
            return


@dataclass
class CursorPage:
    items: list
    next_cursor: 'str | None'
    page_size: int


def _encode_cursor(last_id):
    return base64.urlsafe_b64encode(json.dumps({'id': last_id}).encode('utf-8')).decode('utf-8')


def _decode_cursor(cursor):
    if not cursor:
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode('utf-8')).decode('utf-8'))
        return int(payload['id'])
    except Exception:
        return None


def _cursor_paginate(query, cursor, page_size, serializer, descending):
    page_size = max(1, min(int(page_size or MAX_PAGE_SIZE), MAX_PAGE_SIZE))
    last_id = _decode_cursor(cursor)
    model = query.column_descriptions[0]['entity']
    pk = getattr(model, 'id')
    if last_id is not None:
        query = query.filter(pk < last_id) if descending else query.filter(pk > last_id)
    ordered = query.order_by(pk.desc() if descending else pk.asc())
    rows = ordered.limit(page_size + 1).all()
    has_next = len(rows) > page_size
    page_rows = rows[:page_size]
    items = [serializer(r) for r in page_rows] if serializer else page_rows
    next_cursor = _encode_cursor(page_rows[-1].id) if (has_next and page_rows) else None
    return CursorPage(items=items, next_cursor=next_cursor, page_size=page_size)


def cursor_paginate_asc(query, cursor=None, page_size=MAX_PAGE_SIZE, serializer=None):
    return _cursor_paginate(query, cursor, page_size, serializer, descending=False)


def cursor_paginate_desc(query, cursor=None, page_size=MAX_PAGE_SIZE, serializer=None):
    return _cursor_paginate(query, cursor, page_size, serializer, descending=True)


def build_cursor_pagination_payload(items, next_cursor, page_size):
    return {
        'items': items,
        'next_cursor': next_cursor,
        'page_size': page_size,
        'has_next': next_cursor is not None,
    }


# --- Keyset (cursor) pagination primitives (diagram §6: NEVER OFFSET on hot lists) ---


def get_max_page_size() -> int:
    """Return the hard cap on page size for keyset pagination (env: MAX_PAGE_SIZE)."""
    return _get_max_page_size_from_env()


def encode_keyset_cursor(values, secret: Optional[str] = None) -> str:
    """Encode sort-key values as a tamper-evident cursor.

    When ``secret`` is provided the cursor is ``base64(payload).hmac_sha256``
    so tampering or secret mismatch is detected on decode.
    """
    payload = base64.urlsafe_b64encode(
        json.dumps(values, default=str).encode('utf-8')
    ).decode('utf-8')
    if secret:
        sig = hmac.new(
            secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256
        ).hexdigest()
        return f"{payload}.{sig}"
    return payload


def decode_keyset_cursor(cursor, secret: Optional[str] = None):
    """Decode a keyset cursor, verifying its HMAC signature if a secret was set.

    Returns the original values list, or ``None`` when the cursor is empty,
    malformed, or fails signature verification.
    """
    if not cursor:
        return None
    try:
        if secret:
            _, _, sig = cursor.rpartition(".")
            payload = cursor[:len(cursor) - len(sig) - 1]
            expected = hmac.new(
                secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(sig, expected):
                return None
        else:
            payload = cursor
        decoded = json.loads(base64.urlsafe_b64decode(payload.encode('utf-8')).decode('utf-8'))
        if isinstance(decoded, list):
            return decoded
        return [decoded]
    except Exception:
        return None


def _extract_sort_values(row, sort_keys):
    """Extract sort-key values from a row (entity, scalar tuple, or joined tuple).

    Handles SQLAlchemy 2.0 ``Row`` (not a tuple subclass) as well as ORM entity
    rows and joined ``(Entity, scalar)`` tuples where the sort column lives on
    the entity object rather than the Row itself.
    """
    values = []
    for col, _ in sort_keys:
        attr_name = col.key if hasattr(col, 'key') else col.name if hasattr(col, 'name') else str(col)
        try:
            val = getattr(row, attr_name)
        except (AttributeError, TypeError):
            val = getattr(row[0], attr_name)
        values.append(val)
    return values


def keyset_paginate(query, sort_keys, cursor=None, page_size=MAX_PAGE_SIZE):
    """Keyset (cursor) pagination over a composite sort key.

    ``sort_keys`` is a list of ``(column, direction)`` tuples where direction
    is ``"asc"`` or ``"desc"``. ``cursor`` is a base64-encoded payload from a
    previous call (the ``next_cursor`` value). Returns a dict
    ``{items, next_cursor, page_size, has_next}``.
    """
    page_size = max(1, min(int(page_size or MAX_PAGE_SIZE), MAX_PAGE_SIZE))
    last_keys = decode_keyset_cursor(cursor)

    if last_keys is not None:
        clauses = []
        for i in range(len(sort_keys)):
            col, direction = sort_keys[i]
            op = col.__lt__ if direction == 'desc' else col.__gt__
            eq_clauses = []
            for j in range(i):
                prev_col, _ = sort_keys[j]
                eq_clauses.append(prev_col == last_keys[j])
            eq_clauses.append(op(last_keys[i]))
            clauses.append(and_(*eq_clauses))
        query = query.filter(or_(*clauses))

    order_cols = []
    for col, direction in sort_keys:
        order_cols.append(col.desc() if direction == 'desc' else col.asc())
    ordered = query.order_by(*order_cols)

    rows = ordered.limit(page_size + 1).all()
    has_next = len(rows) > page_size
    page_rows = rows[:page_size]

    next_cursor = None
    if has_next and page_rows:
        key_values = _extract_sort_values(page_rows[-1], sort_keys)
        next_cursor = encode_keyset_cursor(key_values)

    return build_cursor_pagination_payload(page_rows, next_cursor, page_size)


def keyset_offset_window(query, sort_keys, offset, limit):
    """Return rows ``[offset:offset+limit]`` using keyset cursors (never OFFSET).

    This is the migration primitive for adoption-layer list endpoints: they keep
    their ``offset``/``limit`` API, but the window is reached by walking keyset
    cursors (B6 / R6 — never OFFSET on hot lists).

    Works on entity queries, scalar tuples ``(col1, col2)``, and joined tuples
    ``(Entity, scalar)``.
    """
    cursor = None
    # Walk ``offset`` rows one cursor-step at a time to reach the desired offset.
    for _ in range(offset):
        page = keyset_paginate(query, sort_keys, cursor=cursor, page_size=1)
        if not page["items"]:
            return []
        cursor = page["next_cursor"]
        if cursor is None:
            return []

    page = keyset_paginate(query, sort_keys, cursor=cursor, page_size=limit)
    return page["items"]


def keyset_paginated_response(query, sort_keys, cursor=None, page_size=MAX_PAGE_SIZE, *, total=None):
    """Backward-compatible keyset envelope.

    Returns ``{items, next_cursor, page_size, has_next, total, page, pages}``.
    When ``total`` is supplied, ``page`` is ``None`` (cursor-based) and ``pages``
    is ``ceil(total / page_size)``; otherwise both are ``None``.
    """
    page = keyset_paginate(query, sort_keys, cursor=cursor, page_size=page_size)
    result = {
        "items": page["items"],
        "next_cursor": page["next_cursor"],
        "page_size": page["page_size"],
        "has_next": page["has_next"],
        "total": total,
        "page": None,
        "pages": None,
    }
    if total is not None:
        result["pages"] = max(1, (total + page["page_size"] - 1) // page["page_size"])
    return result
