"""Admin/public category controller (LAYER 3).

Thin orchestration over :mod:`services.catalog.category_service`. Translates
service-level ``ValueError`` / missing-row conditions into HTTP semantics so
routers stay declarative.
"""
from __future__ import annotations

from typing import Any, Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy.orm import Query, Session

from data.models import Category
from services.catalog import category_service
import structlog
logger = structlog.get_logger(__name__)

__all__ = [
    "get_category_query",
    "list_categories_page",
    "list_category_summaries",
    "get_category_or_404",
    "get_category_by_ref_or_404",
    "create_category",
    "update_category",
    "deactivate_category",
    "reorder_categories",
]


def get_category_query(
    db: Session,
    *,
    active_only: bool = True,
    parent_id: Optional[int] = None,
    country_code: Optional[str] = None,
) -> Query:
    """Expose the canonical category query for paginated router responses."""
    return category_service.get_category_query(
        db,
        active_only=active_only,
        parent_id=parent_id,
        country_code=country_code,
    )


def list_categories_query(
    db: Session,
    country_code: str,
    *,
    include_deleted: bool = False,
) -> Query:
    """Country-scoped query for the admin categories list endpoint."""
    return category_service.list_categories_query(db, country_code, include_deleted=include_deleted)


def list_categories_page(
    db: Session,
    *,
    active_only: bool = True,
    parent_id: Optional[int] = None,
    country_code: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Return one page of categories in the standard envelope."""
    items, total = category_service.list_categories(
        db,
        active_only=active_only,
        parent_id=parent_id,
        country_code=country_code,
        page=page,
        page_size=page_size,
    )
    return {"data": items, "total": total, "page": page, "page_size": page_size}


def list_category_summaries(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Flat id/slug/commission projection used by admin commission screens."""
    items, total = category_service.list_categories(
        db, active_only=True, page=page, page_size=page_size
    )
    return {
        "data": [category_service.serialize_category_summary(c) for c in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_category_or_404(
    db: Session,
    category_id: int,
    *,
    country_code: Optional[str] = None,
) -> Category:
    """Fetch a category or raise HTTP 404."""
    category = category_service.get_category_by_id(
        db, category_id, country_code=country_code
    )
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


def get_category_by_ref_or_404(db: Session, category_ref: str) -> Category:
    """Resolve a category by slug or id, or raise HTTP 404."""
    category = category_service.get_category_by_ref(db, category_ref)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


def get_country_category_or_404(
    db: Session, category_id: int, country_code: str
) -> Category:
    """Fetch a category scoped to a country or raise HTTP 404."""
    return get_category_or_404(db, category_id, country_code=country_code)


def create_category(db: Session, payload: dict[str, Any], *, rebuild_paths: bool = False) -> Category:
    """Create a category, mapping duplicate slugs to HTTP 409."""
    try:
        return category_service.create_category(db, payload, rebuild_paths=rebuild_paths)
    except ValueError as exc:
        logger.exception("create_category_failed", error=str(exc))
        detail = str(exc)
        code = (
            status.HTTP_409_CONFLICT
            if "already exists" in detail
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code=code, detail=detail) from exc


def update_category(
    db: Session,
    category: Category,
    updates: dict[str, Any],
    *,
    rebuild_paths: bool = False,
) -> Category:
    """Update a category, mapping duplicate slugs to HTTP 409."""
    try:
        return category_service.update_category(
            db, category, updates, rebuild_paths=rebuild_paths
        )
    except ValueError as exc:
        logger.exception("update_category_failed", error=str(exc))
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def deactivate_category(db: Session, category: Category) -> Category:
    """Soft-delete a category."""
    return category_service.deactivate_category(db, category)


def reorder_categories(db: Session, order: dict[Any, Any]) -> int:
    """Bulk-assign sort order; returns the number of rows updated."""
    if not order:
        raise HTTPException(status_code=422, detail="order payload is required")
    try:
        normalized = {int(k): int(v) for k, v in order.items()}
    except (TypeError, ValueError) as exc:
        logger.exception("reorder_categories_failed", error=str(exc))
        raise HTTPException(
            status_code=422, detail="order must map category id -> sort order"
        ) from exc
    return category_service.reorder_categories(db, normalized)
