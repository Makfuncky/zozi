"""Service methods for category read operations."""
from typing import List
from sqlalchemy.orm import Session
from data.models import Category, Product


def list_categories(db: Session) -> list[Category]:
    """List root-level categories."""
    return db.query(Category).filter(Category.parent_id.is_(None)).order_by(Category.sort_order).all()


def get_category_by_id(db: Session, category_id: int | None = None, slug: str | None = None) -> Category | None:
    """Get category by ID or slug."""
    q = db.query(Category)
    if category_id:
        q = q.filter(Category.id == category_id)
    if slug:
        q = q.filter(Category.slug == slug)
    return q.first()


def get_category_tree(db: Session) -> list[dict]:
    """Get category tree structure."""
    roots = list_categories(db)
    tree = []
    for root in roots:
        children = db.query(Category).filter(Category.parent_id == root.id).all()
        tree.append({
            "id": root.id,
            "name": root.name,
            "slug": root.slug,
            "children": [{"id": c.id, "name": c.name, "slug": c.slug} for c in children],
        })
    return tree


def get_products_in_category(db: Session, category_id: int, skip: int = 0, limit: int = 20) -> list[Product]:
    """Get products in a category."""
    return (
        db.query(Product)
        .filter(Product.category_id == category_id, Product.is_active == True)
        .order_by(Product.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
