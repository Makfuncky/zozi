"""Category domain service (LAYER 4).

Single owner of every read and write against the ``commerce.categories``
table. Routers and controllers MUST delegate here instead of touching the
session directly (audit rules LC1 / W1 / Q1).

Historical damage this module repairs
-------------------------------------
``services/products_write_service.py`` used to re-export ``create_category`` /
``update_category`` / ``delete_category`` from ``services.security.permission_service``.
Those functions operate on :class:`PermissionCategory` (an RBAC grouping), not
on the storefront :class:`Category`. Every admin category write therefore
raised ``TypeError`` at runtime, and ``reorder_categories`` was wired back to
the *router endpoint itself* (``routers.admin_categories_governance.reorder_categories``),
creating both an upward Layer 4 -> Layer 2 import and a circular import.

All of that logic now lives here, against the correct model.
"""
from __future__ import annotations

import logging
from typing import Any, Iterable, Mapping, Optional, Sequence

from sqlalchemy.orm import Query, Session

from domains.catalog.models.products import Category
from infrastructure.utils.slug import generate_slug
from domains.catalog.utils.category_tree import (
    _chain_for,
    compute_category_path,
    rebuild_category_paths,
    category_subtree_ids,
)
import structlog
logger = structlog.get_logger(__name__)

# Columns a caller is allowed to set. Anything else in a payload is ignored so
# an over-posted request can never write to `id`, `path`, `depth`, timestamps…
_WRITABLE_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "description",
        "parent_id",
        "icon",
        "image_url",
        "is_active",
        "is_featured",
        "sort_order",
        "commission_rate",
        "meta_title",
        "meta_description",
        "country_code",
    }
)

__all__ = [
    "get_category_query",
    "list_categories",
    "get_category_by_ref",
    "get_category_by_id",
    "category_slug_exists",
    "create_category",
    "build_category_payload",
    "update_category",
    "build_category_updates",
    "deactivate_category",
    "delete_category",
    "reorder_categories",
    "serialize_category_summary",
    "rebuild_category_paths",
    "category_subtree_ids",
    "category_subtree_ids_inclusive",
    "list_categories_flat",
    "archive_category",
    "restore_category",
    "bulk_archive_categories",
    "bulk_restore_categories",
    "update_category_by_id",
    "delete_category_by_id",
]


# ── Reads ─────────────────────────────────────────────────────────────────────


def get_category_query(
    db: Session,
    *,
    active_only: bool = True,
    parent_id: Optional[int] = None,
    country_code: Optional[str] = None,
) -> Query:
    """Build the canonical ordered ``Category`` query.

    Returned as a :class:`~sqlalchemy.orm.Query` (not a list) so callers can
    hand it to :func:`infrastructure.utils.pagination.paginated_response` without loading the
    whole table — this is what keeps the list endpoints bounded (PERF4).
    """
    query = db.query(Category)
    if active_only:
        query = query.filter(Category.is_active.is_(True))
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    if country_code:
        query = query.filter(Category.country_code == country_code.upper())
    return query.order_by(Category.sort_order, Category.name)


def list_categories_query(
    db: Session,
    country_code: str,
    *,
    include_deleted: bool = False,
) -> Query:
    """Country-scoped ordered query for the admin categories list endpoint."""
    return get_category_query(
        db,
        active_only=not include_deleted,
        country_code=country_code,
    )


def list_categories(
    db: Session,
    *,
    active_only: bool = True,
    parent_id: Optional[int] = None,
    country_code: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[Category], int]:
    """Return ``(items, total)`` for one page of categories."""
    from infrastructure.utils.pagination import paginated_query  # local: avoids import cycle

    query = get_category_query(
        db,
        active_only=active_only,
        parent_id=parent_id,
        country_code=country_code,
    )
    return paginated_query(query, page, page_size)


def get_category_by_id(
    db: Session,
    category_id: int,
    *,
    country_code: Optional[str] = None,
) -> Optional[Category]:
    """Fetch a single category by primary key."""
    query = db.query(Category).filter(Category.id == category_id)
    if country_code:
        query = query.filter(Category.country_code == country_code.upper())
    return query.first()


def get_category_by_ref(db: Session, category_ref: str) -> Optional[Category]:
    """Resolve a category by slug, falling back to numeric id."""
    category = db.query(Category).filter(Category.slug == category_ref).first()
    if category is None and str(category_ref).isdigit():
        category = get_category_by_id(db, int(category_ref))
    return category


def category_slug_exists(
    db: Session,
    slug: str,
    *,
    exclude_id: Optional[int] = None,
) -> bool:
    """Return True when ``slug`` is already taken by another category."""
    query = db.query(Category.id).filter(Category.slug == slug)
    if exclude_id is not None:
        query = query.filter(Category.id != exclude_id)
    return db.query(query.exists()).scalar() is True


def serialize_category_summary(category: Category) -> dict[str, Any]:
    """Flat projection used by admin commission configuration screens."""
    commission_rate = getattr(category, "commission_rate", None)
    return {
        "id": category.id,
        "slug": category.slug,
        "name": category.name,
        "parent_id": category.parent_id,
        "commission_rate": float(commission_rate) if commission_rate is not None else None,
        "sort_order": category.sort_order,
    }


# ── Writes ────────────────────────────────────────────────────────────────────


def _apply_fields(category: Category, values: Mapping[str, Any]) -> None:
    """Copy only whitelisted, non-None keys onto the ORM instance."""
    for field, value in values.items():
        if field in _WRITABLE_FIELDS and value is not None:
            setattr(category, field, value)


def create_category(
    db: Session,
    payload: Mapping[str, Any],
    *,
    rebuild_paths: bool = False,
) -> Category:
    """Create a category, generating a unique slug when one is not supplied.

    ``payload`` is an allow-listed dict (name, slug, parent_id, sort_order,
    description, country_code, ...). Unknown keys are ignored.

    Raises:
        ValueError: when ``name`` is blank or the resolved slug already exists.
    """
    data = dict(payload or {})
    clean_name = str(data.get("name") or "").strip()
    if not clean_name:
        raise ValueError("Category name is required")

    slug = data.get("slug")
    resolved_slug = generate_slug(slug or clean_name)
    if category_slug_exists(db, resolved_slug):
        raise ValueError("Category slug already exists")

    category = Category(name=clean_name, slug=resolved_slug)
    _apply_fields(category, data)

    db.add(category)
    db.commit()
    db.refresh(category)

    if rebuild_paths:
        rebuild_category_paths(db)

    logger.info("category.created id=%s slug=%s", category.id, category.slug)
    return category


def build_category_payload(
    *,
    name: str | None = None,
    slug: str | None = None,
    parent_id: int | None = None,
    sort_order: int = 0,
    description: str | None = None,
    country_code: str | None = None,
) -> dict[str, Any]:
    """Build a normalized category payload dict from raw request data.

    Country code is uppercased for storage consistency.
    """
    return {
        "name": name,
        "slug": slug,
        "parent_id": parent_id,
        "sort_order": sort_order,
        "description": description,
        "country_code": country_code.upper() if country_code else country_code,
    }


def build_category_updates(
    *,
    name: str | None = None,
    slug: str | None = None,
    parent_id: int | None = None,
    sort_order: int | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Build a filtered updates dict, excluding unset (None) fields."""
    updates: dict[str, Any] = {}
    if name is not None:
        updates["name"] = name
    if slug is not None:
        updates["slug"] = slug
    if parent_id is not None:
        updates["parent_id"] = parent_id
    if sort_order is not None:
        updates["sort_order"] = sort_order
    if description is not None:
        updates["description"] = description
    return updates


def update_category(
    db: Session,
    category: Category,
    updates: Mapping[str, Any],
    *,
    rebuild_paths: bool = False,
) -> Category:
    """Apply ``updates`` to an existing category and persist them.

    Raises:
        ValueError: when a requested slug collides with another category.
    """
    payload = dict(updates or {})
    requested_slug = payload.pop("slug", None)

    if requested_slug is not None:
        resolved_slug = generate_slug(requested_slug)
        if category_slug_exists(db, resolved_slug, exclude_id=int(category.id)):
            raise ValueError("Category slug already exists")
        category.slug = resolved_slug

    _apply_fields(category, payload)

    db.commit()
    db.refresh(category)

    if rebuild_paths:
        rebuild_category_paths(db)

    logger.info("category.updated id=%s", category.id)
    return category


def deactivate_category(db: Session, category: Category) -> Category:
    """Soft-delete a category by clearing ``is_active``.

    ``commerce.categories`` has no ``is_deleted`` column, so deactivation is
    the soft-delete contract for this table.
    """
    category.is_active = False
    db.commit()
    db.refresh(category)
    logger.info("category.deactivated id=%s", category.id)
    return category


# Public alias: routers speak "delete", the table semantics are "deactivate".
delete_category = deactivate_category


def update_category_by_id(
    db: Session,
    country_code: str,
    category_id: int,
    updates: Mapping[str, Any],
    *,
    rebuild_paths: bool = True,
) -> Category:
    """Fetch a category by id + country and apply updates. Raises 404 if missing."""
    from fastapi import HTTPException

    category = get_category_by_id(db, category_id, country_code=country_code)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return update_category(db, category, updates, rebuild_paths=rebuild_paths)


def delete_category_by_id(db: Session, country_code: str, category_id: int) -> dict:
    """Fetch a category by id + country and deactivate it. Raises 404 if missing."""
    from fastapi import HTTPException

    category = get_category_by_id(db, category_id, country_code=country_code)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    delete_category(db, category)
    return {"message": "Category deleted"}


def reorder_categories(db: Session, order: Mapping[int, int]) -> int:
    """Bulk-assign ``sort_order`` values.

    Args:
        order: mapping of ``category_id -> sort_order``.

    Returns:
        Number of categories actually updated.
    """
    if not order:
        return 0

    ids: Iterable[int] = [int(k) for k in order.keys()]
    categories = db.query(Category).filter(Category.id.in_(list(ids))).all()

    updated = 0
    for category in categories:
        new_order = order.get(category.id, order.get(str(category.id)))
        if new_order is None:
            continue
        category.sort_order = int(new_order)
        updated += 1

    db.commit()
    logger.info("category.reordered count=%s", updated)
    return updated


# ── Materialized-path helpers (Phase 3a) ──────────────────────────────────────
# Category depth is shallow (<=5) and changes rarely; a materialized path
# (path="/1/15/42/", depth=2) enables O(1) sub-tree queries via LIKE instead
# of recursive CTEs. Nested-set would force a full renumber on every insert.
# These helpers are imported from domains.catalog.utils.category_tree.


def category_subtree_ids_inclusive(category_id: int, db: Session) -> list[int]:
    """Return ids of the category and all of its descendants."""
    ids = category_subtree_ids(category_id, db)
    ids.append(int(category_id))
    return ids


def list_categories_flat(
    db: Session,
    *,
    active_only: bool = True,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """Flat projection of categories for admin commission configuration screens.

    Returns ``{data, total, page, page_size}`` where each row carries the
    fields a commission grid needs: id, slug, name, parent_id, commission_rate,
    sort_order.
    """
    from infrastructure.utils.pagination import paginated_query  # local: avoids import cycle

    query = get_category_query(db, active_only=active_only)
    items, total = paginated_query(query, page, page_size)
    return {
        "data": [serialize_category_summary(c) for c in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ── Archive / restore / bulk (folded from admin_categories_service) ──────────
# These delegate to the generic governance archive/restore helpers. Kept here
# (rather than in the router) so the router stays thin (Law 2).


def archive_category(category_id: int, acting_user: dict, db: Session, *, reason: Optional[str] = None) -> dict:
    """Soft-archive a category."""
    from domains.governance.services.settings.misc_service import archive_entity

    return archive_entity("category", category_id, acting_user, db, reason)


def restore_category(category_id: int, acting_user: dict, db: Session) -> dict:
    """Restore a soft-archived category."""
    from domains.governance.services.settings.misc_service import restore_entity

    return restore_entity("category", category_id, acting_user, db)


def bulk_archive_categories(ids: list[int], acting_user: dict, db: Session, *, reason: Optional[str] = None) -> dict:
    """Archive many categories."""
    from domains.catalog.services.products.bulk_ops_write_service import bulk_archive_entities

    return bulk_archive_entities(db, Category, ids, acting_user, reason)


def bulk_restore_categories(ids: list[int], acting_user: dict, db: Session) -> dict:
    """Restore many categories."""
    from domains.catalog.services.products.bulk_ops_write_service import bulk_restore_entities

    return bulk_restore_entities(db, Category, ids, acting_user)
