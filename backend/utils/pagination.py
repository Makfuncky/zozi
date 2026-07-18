"""
Pagination utilities — standardized helpers used across routers.

Usage in a router::

    from utils.pagination import PageParams, apply_pagination, set_total_count_header

    @router.get("/items")
    def list_items(page: PageParams = Depends(), response: Response = None, db: Session = Depends(get_db)):
        query = db.query(Item)
        total = query.count()
        items = apply_pagination(query, page).all()
        set_total_count_header(response, total)
        return items
"""
from __future__ import annotations

from typing import TypeVar

from fastapi import Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Query as SAQuery

from utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

_Q = TypeVar("_Q")


class PageParams(BaseModel):
    """Reusable pagination query parameters."""

    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
    offset: int = Query(default=0, ge=0)


def apply_pagination(query: SAQuery, params: PageParams) -> SAQuery:  # type: ignore[type-arg]
    """Apply ``limit`` / ``offset`` to a SQLAlchemy query."""
    return query.offset(params.offset).limit(params.limit)


def paginate(query: SAQuery, page: int, size: int) -> dict:
    """Legacy pagination API retained for older routers/tests."""
    safe_page = max(int(page or 1), 1)
    safe_size = max(int(size or DEFAULT_PAGE_SIZE), 1)
    total = query.count()
    pages = (total + safe_size - 1) // safe_size if total else 1
    items = query.offset((safe_page - 1) * safe_size).limit(safe_size).all()
    return {
        "items": items,
        "total": total,
        "page": safe_page,
        "size": safe_size,
        "pages": pages,
    }


def set_total_count_header(response: Response | None, total: int) -> None:
    """Write the ``X-Total-Count`` header so the frontend can render pagination."""
    if response is not None:
        response.headers["X-Total-Count"] = str(total)

