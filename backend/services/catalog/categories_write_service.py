"""Service methods for category write operations."""
from sqlalchemy.orm import Session
from data.models import Category
from data.services_write_helpers import add_and_flush, delete_and_flush, commit_and_refresh


def create_category(db: Session, name: str, parent_id: int | None = None) -> Category:
    """Create a new category."""
    cat = Category(name=name, parent_id=parent_id)
    add_and_flush(db, cat)
    db.commit()
    db.refresh(cat)
    return cat


def create_category_with_slug(db: Session, name: str, slug: str, parent_id: int | None = None, **extra_fields) -> Category:
    """Create a new category with a pre-computed slug and extra fields."""
    cat = Category(name=name, slug=slug, parent_id=parent_id, **extra_fields)
    add_and_flush(db, cat)
    commit_and_refresh(db, cat)
    return cat


def update_category(db: Session, category_id: int, **kwargs) -> Category | None:
    """Update a category."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        return None
    for key, value in kwargs.items():
        if hasattr(cat, key):
            setattr(cat, key, value)
    db.commit()
    db.refresh(cat)
    return cat


def update_category_full(db: Session, category_id: int, updates: dict) -> Category | None:
    """Update a category with a pre-built updates dict, committing and refreshing."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        return None
    for key, value in updates.items():
        if hasattr(cat, key):
            setattr(cat, key, value)
    commit_and_refresh(db, cat)
    return cat


def deactivate_category(db: Session, category_id: int) -> bool:
    """Soft-deactivate a category."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        return False
    cat.is_active = False
    db.commit()
    return True


def delete_category(db: Session, category_id: int) -> bool:
    """Delete a category."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        return False
    db.delete(cat)
    db.commit()
    return True
