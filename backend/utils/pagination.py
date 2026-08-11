"""Safe pagination helpers for list endpoints.

Enforces hard caps so an unbounded query never OOMs the server.
"""
from __future__ import annotations

from typing import Any, Callable, Iterator, Optional, Sequence

from sqlalchemy import func
from sqlalchemy.orm import Query

# Hard cap on page size — any request above this is silently clamped.
MAX_PAGE_SIZE = 100
MAX_EXPORT_SIZE = 5000

# Absolute hard limit for any single query to prevent OOM.
SAFE_QUERY_LIMIT = 1000


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

import base64
import json
from dataclasses import dataclass

from sqlalchemy.orm import Query


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
