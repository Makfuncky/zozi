"""Categories service — DB read/write operations for product categories."""
from typing import Optional

from sqlalchemy.orm import Session

from data.models import Category


def get_category_query(db: Session, active_only: bool = True, parent_id: Optional[int] = None):
    """Return a base Category query optionally filtered by active/parent."""
    query = db.query(Category)
    if active_only:
        query = query.filter(Category.is_active == True)
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    return query


def get_category_by_ref(db: Session, category_ref: str) -> Optional[Category]:
    """Fetch a category by slug, falling back to integer id."""
    cat = db.query(Category).filter(Category.slug == category_ref).first()
    if not cat and category_ref.isdigit():
        cat = db.query(Category).filter(Category.id == int(category_ref)).first()
    return cat


def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
    return db.query(Category).filter(Category.id == category_id).first()


def category_slug_exists(db: Session, slug: str, exclude_id: Optional[int] = None) -> bool:
    q = db.query(Category).filter(Category.slug == slug)
    if exclude_id is not None:
        q = q.filter(Category.id != exclude_id)
    return q.first() is not None


def create_category(db: Session, name: str, slug: str, **fields) -> Category:
    cat = Category(name=name, slug=slug)
    for field_name, value in fields.items():
        setattr(cat, field_name, value)
    db.add(cat)
    db.flush()
    db.commit()
    db.refresh(cat)
    return cat


def update_category(db: Session, cat: Category, updates: dict) -> Category:
    for k, v in updates.items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat


def deactivate_category(db: Session, cat: Category) -> None:
    cat.is_active = False
    db.commit()
