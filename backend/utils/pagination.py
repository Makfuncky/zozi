"""Safe pagination helpers for list endpoints.

Enforces hard caps so an unbounded query never OOMs the server.
"""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Callable, Optional, Sequence

from sqlalchemy import asc, desc
from sqlalchemy.orm import Query

MAX_PAGE_SIZE = 100
MAX_EXPORT_SIZE = 5000


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


@dataclass
class CursorPage:
    """Cursor-based pagination response model.

    Unlike offset pagination, cursor pagination uses a cursor (opaque token)
    representing the last seen item. This enables efficient pagination
    without scanning skipped rows.
    """

    items: list[Any]
    next_cursor: Optional[str] = None
    has_more: bool = False
    page_size: int = MAX_PAGE_SIZE


def encode_cursor(**kwargs: Any) -> str:
    """Encode cursor parameters into an opaque base64 string."""
    raw = json.dumps(kwargs, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str, **expected_keys: Any) -> dict[str, Any]:
    """Decode a cursor string into its components.

    Args:
        cursor: Base64-encoded cursor string
        **expected_keys: Expected keys (value ignored, used for type hints)

    Returns:
        Dictionary of decoded cursor values
    """
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        data = json.loads(raw)
        result = {}
        for key in expected_keys:
            result[key] = data.get(key)
        return result
    except Exception:
        return {}


def cursor_paginate(
    query: Query,
    cursor: Optional[str] = None,
    page_size: int = MAX_PAGE_SIZE,
    sort_desc: bool = False,
    serializer: Optional[Callable[[Any], dict]] = None,
    id_field: Optional[str] = "id",
) -> CursorPage:
    """Execute a cursor-based paginated query.

    Args:
        query: SQLAlchemy Query object, already filtered to desired result set
        cursor: Opaque cursor token from previous page (contains last seen id)
        page_size: Maximum number of items to return (capped at MAX_PAGE_SIZE)
        sort_desc: If True, use ID < cursor for DESC; if False, ID > cursor for ASC
        serializer: Optional function to transform each item
        id_field: Name of the ID field to use for cursor filtering (default: "id")

    Returns:
        CursorPage with items, next_cursor, and has_more flag
    """
    page_size = min(page_size, MAX_PAGE_SIZE)

    query = query.limit(page_size + 1)

    if cursor:
        decoded = decode_cursor(cursor, id=0)
        last_id = decoded.get("id")
        if last_id is not None:
            if sort_desc:
                query = query.filter(getattr(query.column_descriptions[0]["entity"], id_field) < last_id)
            else:
                query = query.filter(getattr(query.column_descriptions[0]["entity"], id_field) > last_id)

    rows = query.all()

    has_more = len(rows) > page_size
    items = rows[:page_size]

    if serializer:
        items = [serializer(item) for item in items]

    next_cursor = None
    if has_more:
        last_item = rows[page_size - 1]
        last_id = getattr(last_item, "id", None)
        if last_id is not None:
            next_cursor = encode_cursor(id=last_id)

    return CursorPage(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        page_size=page_size,
    )


def cursor_paginate_desc(
    query: Query,
    cursor: Optional[str] = None,
    page_size: int = MAX_PAGE_SIZE,
    serializer: Optional[Callable[[Any], dict]] = None,
) -> CursorPage:
    """Cursor-based pagination optimized for DESC ordering (newest first).

    Uses ID < cursor for efficient reverse ordering pagination.
    """
    return cursor_paginate(
        query=query,
        cursor=cursor,
        page_size=page_size,
        sort_desc=True,
        serializer=serializer,
    )


def cursor_paginate_asc(
    query: Query,
    cursor: Optional[str] = None,
    page_size: int = MAX_PAGE_SIZE,
    serializer: Optional[Callable[[Any], dict]] = None,
) -> CursorPage:
    """Cursor-based pagination optimized for ASC ordering (oldest first).

    Uses ID > cursor for efficient forward ordering pagination.
    """
    return cursor_paginate(
        query=query,
        cursor=cursor,
        page_size=page_size,
        sort_desc=False,
        serializer=serializer,
    )


def build_cursor_pagination_payload(items: list, next_cursor: Optional[str], page_size: int) -> dict:
    """Build a cursor pagination response payload.

    Args:
        items: List of serialized items
        next_cursor: Cursor for next page (or None)
        page_size: Page size used

    Returns:
        Dict with items, nextCursor, hasMore, pageSize
    """
    return {
        "items": items,
        "nextCursor": next_cursor,
        "hasMore": next_cursor is not None,
        "pageSize": page_size,
    }