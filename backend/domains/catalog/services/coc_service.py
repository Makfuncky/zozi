from __future__ import annotations

"""Chart of Categories (CoC) Service.

Manages the 7-layer taxonomy system:
- Levels 1-3: Strict relational nodes (ChartOfCategory)
- Level 4: Product Types
- Levels 5-6: Category Attributes
- Level 7: SKU/Leaf (product variants)
"""
import json
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from domains.catalog.models.chart_of_categories import (
    CategoryAttribute,
    ChartOfCategory,
    ProductType,
)

logger = logging.getLogger(__name__)


# ── Tree Operations ────────────────────────────────────────────────────────


def get_category_tree(
    db: Session,
    *,
    parent_id: Optional[int] = None,
    max_depth: int = 3,
    include_inactive: bool = False,
) -> list[dict]:
    """Get the category tree starting from a parent node.

    Cached for 24 hours via Valkey under the ``coc`` namespace — invalidation
    is driven by ``bump_cache_version("coc")`` on create/update/archive/restore.

    Args:
        db: Database session.
        parent_id: Starting parent ID (None for root).
        max_depth: Maximum depth to traverse.
        include_inactive: Include inactive categories.

    Returns:
        List of category dicts with nested children.
    """
    from infrastructure.utils.cache import cache_or_compute

    payload = {
        "parent_id": parent_id,
        "max_depth": max_depth,
        "include_inactive": include_inactive,
    }

    def _compute() -> list[dict]:
        query = db.query(ChartOfCategory).filter(
            ChartOfCategory.parent_id == parent_id,
            ChartOfCategory.is_deleted.is_(False),
        )
        if not include_inactive:
            query = query.filter(ChartOfCategory.is_active.is_(True))
        nodes = query.order_by(ChartOfCategory.sort_order, ChartOfCategory.name).all()
        result = []
        for node in nodes:
            cat_dict = _node_to_dict(node)
            if max_depth > 1 and node.level < 3:
                cat_dict["children"] = get_category_tree(
                    db,
                    parent_id=node.id,
                    max_depth=max_depth - 1,
                    include_inactive=include_inactive,
                )
            result.append(cat_dict)
        return result

    try:
        import hashlib
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:16]
        return cache_or_compute(
            f"category_tree:{digest}",
            _compute,
            ttl=24 * 60 * 60,  # 24 hours
            namespace="coc",
        )
    except Exception:
        # Cache failure must never block a read.
        return _compute()


def get_category_by_id(db: Session, category_id: int) -> Optional[ChartOfCategory]:
    """Get a category by ID."""
    return db.query(ChartOfCategory).filter(
        ChartOfCategory.id == category_id,
        ChartOfCategory.is_deleted.is_(False),
    ).first()


def create_category(
    db: Session,
    *,
    name: str,
    slug: str,
    level: int,
    parent_id: Optional[int] = None,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    sort_order: int = 0,
    commission_group_id: Optional[int] = None,
) -> ChartOfCategory:
    """Create a new category node."""
    # Validate parent exists
    if parent_id:
        parent = get_category_by_id(db, parent_id)
        if not parent:
            raise ValueError(f"Parent category {parent_id} not found")
        if parent.level >= level:
            raise ValueError(f"Level must be greater than parent level ({parent.level})")

    # Build materialized path
    path = _build_path(db, parent_id, slug)

    category = ChartOfCategory(
        name=name,
        slug=slug,
        level=level,
        parent_id=parent_id,
        description=description,
        icon=icon,
        sort_order=sort_order,
        path=path,
        depth=level - 1,
        commission_group_id=commission_group_id,
    )

    db.add(category)
    db.commit()

    logger.info("category.coc.created id=%s name=%s level=%s", category.id, name, level)
    return category


def update_category(
    db: Session,
    category_id: int,
    **updates: Any,
) -> Optional[ChartOfCategory]:
    """Update a category node."""
    category = get_category_by_id(db, category_id)
    if not category:
        return None

    for key, value in updates.items():
        if hasattr(category, key):
            setattr(category, key, value)

    db.commit()
    logger.info("category.coc.updated id=%s", category_id)
    return category


def archive_category(db: Session, category_id: int) -> bool:
    """Soft-delete a category (archive)."""
    category = get_category_by_id(db, category_id)
    if not category:
        return False

    category.is_deleted = True
    category.is_active = False
    db.commit()

    logger.info("category.coc.archived id=%s", category_id)
    return True


def restore_category(db: Session, category_id: int) -> bool:
    """Restore an archived category."""
    category = db.query(ChartOfCategory).filter(
        ChartOfCategory.id == category_id,
    ).first()

    if not category:
        return False

    category.is_deleted = False
    category.is_active = True
    db.commit()

    logger.info("category.coc.restored id=%s", category_id)
    return True


def toggle_category_active(
    db: Session,
    category_id: int,
    is_active: bool,
) -> Optional[ChartOfCategory]:
    """Toggle category active status."""
    category = get_category_by_id(db, category_id)
    if not category:
        return None

    category.is_active = is_active
    db.commit()

    logger.info("category.coc.toggled id=%s active=%s", category_id, is_active)
    return category


# ── Search ─────────────────────────────────────────────────────────────────


def search_categories(
    db: Session,
    query: str,
    *,
    limit: int = 20,
    include_inactive: bool = False,
) -> list[dict]:
    """Search categories by name or slug."""
    sql_query = db.query(ChartOfCategory).filter(
        ChartOfCategory.is_deleted.is_(False),
        (ChartOfCategory.name.ilike(f"%{query}%")) | (ChartOfCategory.slug.ilike(f"%{query}%")),
    )

    if not include_inactive:
        sql_query = sql_query.filter(ChartOfCategory.is_active.is_(True))

    nodes = sql_query.order_by(ChartOfCategory.level, ChartOfCategory.name).limit(limit).all()

    return [_node_to_dict(node) for node in nodes]


# ── Product Types (Level 4) ────────────────────────────────────────────────


def get_product_types(
    db: Session,
    coc_category_id: int,
    *,
    include_inactive: bool = False,
) -> list[ProductType]:
    """Get product types for a Level 3 category."""
    query = db.query(ProductType).filter(
        ProductType.coc_category_id == coc_category_id,
    )

    if not include_inactive:
        query = query.filter(ProductType.is_active.is_(True))

    return query.order_by(ProductType.sort_order, ProductType.name).all()


def create_product_type(
    db: Session,
    *,
    coc_category_id: int,
    name: str,
    slug: str,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    attribute_schema: Optional[list[dict]] = None,
) -> ProductType:
    """Create a new product type."""
    pt = ProductType(
        coc_category_id=coc_category_id,
        name=name,
        slug=slug,
        description=description,
        icon=icon,
        attribute_schema=json.dumps(attribute_schema) if attribute_schema else None,
    )

    db.add(pt)
    db.commit()

    logger.info("category.product_type.created id=%s name=%s", pt.id, name)
    return pt


# ── Attributes (Levels 5-6) ────────────────────────────────────────────────


def get_attributes(
    db: Session,
    product_type_id: int,
    *,
    layer: Optional[int] = None,
) -> list[CategoryAttribute]:
    """Get attributes for a product type."""
    query = db.query(CategoryAttribute).filter(
        CategoryAttribute.product_type_id == product_type_id,
        CategoryAttribute.is_active.is_(True),
    )

    if layer:
        query = query.filter(CategoryAttribute.layer == layer)

    return query.order_by(CategoryAttribute.layer, CategoryAttribute.sort_order).all()


def create_attribute(
    db: Session,
    *,
    product_type_id: int,
    name: str,
    key: str,
    layer: int,
    value_type: str = "select",
    options: Optional[list[str]] = None,
    is_required: bool = False,
    is_filterable: bool = True,
) -> CategoryAttribute:
    """Create a new category attribute."""
    attr = CategoryAttribute(
        product_type_id=product_type_id,
        name=name,
        key=key,
        layer=layer,
        value_type=value_type,
        options=json.dumps(options) if options else None,
        is_required=is_required,
        is_filterable=is_filterable,
    )

    db.add(attr)
    db.commit()

    logger.info("category.attribute.created id=%s name=%s layer=%s", attr.id, name, layer)
    return attr


# ── Helpers ────────────────────────────────────────────────────────────────


def _node_to_dict(node: ChartOfCategory) -> dict:
    """Convert a category node to a dict."""
    return {
        "id": node.id,
        "name": node.name,
        "slug": node.slug,
        "level": node.level,
        "description": node.description,
        "icon": node.icon,
        "sort_order": node.sort_order,
        "is_active": node.is_active,
        "is_deleted": node.is_deleted,
        "parent_id": node.parent_id,
        "path": node.path,
        "depth": node.depth,
        "commission_group_id": node.commission_group_id,
        "children": [],
    }


def _build_path(db: Session, parent_id: Optional[int], slug: str) -> str:
    """Build the materialized path for a category."""
    if not parent_id:
        return f"/{slug}/"

    parent = db.query(ChartOfCategory).filter(ChartOfCategory.id == parent_id).first()
    if not parent:
        return f"/{slug}/"

    return f"{parent.path}{slug}/"
