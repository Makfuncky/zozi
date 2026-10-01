"""Seed script for comprehensive category taxonomy.

Loads the full category taxonomy from the **canonical Python seed module**
(``infrastructure.database.seed._seed_constants.CATEGORIES``) into the database.
The taxonomy is mirrored to the legacy ``categories_full.json`` for any
downstream tool that still reads the JSON; the Python module is the
canonical source of truth.

The production seed path is ``infrastructure.database.seed._common.seed_data()``
which inserts directly into the Neon PostgreSQL tables via SQLAlchemy ORM.
This script is a dev-only offline tool.

Usage:
    python -m scripts.seed_categories                    # seed all countries
    python -m scripts.seed_categories --country AE        # seed specific country
    python -m scripts.seed_categories --dry-run           # preview without writing
    python -m scripts.seed_categories --deactivate       # deactivate missing categories
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# Ensure backend is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.utils.category_tree import rebuild_category_paths
from domains.catalog.models.products import Category

# Import all domain models and configure mappers so cross-domain
# relationships (e.g., User → Referral) resolve correctly.
import importlib
import pkgutil

def _configure_mappers():
    """Import all domain models and configure SQLAlchemy mappers."""
    for _d in (
        "accounts", "catalog", "orders", "finance", "suppliers", "logistics",
        "comms", "hr", "promotions", "security", "governance", "analytics",
        "country", "customers", "audit",
    ):
        _pkg_name = f"domains.{_d}.models"
        try:
            pkg = importlib.import_module(_pkg_name)
        except Exception:
            continue
        for _m in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
            try:
                importlib.import_module(_m.name)
            except Exception:
                pass
    # Import cross-domain relationship targets
    from domains.customers.models.customer_schema_models import Referral  # noqa: F401
    from domains.country.models.countries import CountryConfig  # noqa: F401
    from sqlalchemy.orm import configure_mappers
    configure_mappers()

_configure_mappers()


def _flatten_taxonomy(
    nodes: list[dict],
    *,
    parent_id: int | None = None,
    flat: list[dict] | None = None,
) -> list[dict]:
    """Flatten nested taxonomy into a list with parent_id references.

    Does NOT mutate the input data (uses .get() instead of .pop()).
    """
    if flat is None:
        flat = []
    for node in nodes:
        children = node.get("children", [])
        flat.append({
            "id": node["id"],
            "name": node["name"],
            "slug": node["slug"],
            "icon": node.get("icon"),
            "sort_order": node.get("sort_order", 0),
            "is_active": node.get("is_active", True),
            "parent_id": parent_id,
            "description": node.get("description"),
            "image_url": node.get("image_url"),
            "is_featured": node.get("is_featured", False),
            "commission_rate": node.get("commission_rate"),
            "meta_title": node.get("meta_title"),
            "meta_description": node.get("meta_description"),
        })
        if children:
            _flatten_taxonomy(children, parent_id=node["id"], flat=flat)
    return flat


def _load_taxonomy_data() -> list[dict]:
    """Load the full taxonomy from the canonical Python seed constants module.

    Falls back to the legacy ``categories_full.json`` for offline dev tools
    if the constants module is unavailable.
    """
    try:
        from infrastructure.database.seed import _seed_constants
        return list(_seed_constants.CATEGORIES)
    except (ImportError, AttributeError):
        seed_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "infrastructure", "database", "seed_data", "categories_full.json",
        )
        with open(seed_path, "r", encoding="utf-8") as f:
            return json.load(f)


def seed_categories(
    db: Session,
    *,
    country_code: str | None = None,
    dry_run: bool = False,
    deactivate_missing: bool = False,
    clear_first: bool = False,
) -> dict[str, int]:
    """Seed categories from the full taxonomy.

    Args:
        db: Database session.
        country_code: If provided, scope to this country. Otherwise seed globally.
        dry_run: If True, count without writing.
        deactivate_missing: If True, deactivate categories not in the taxonomy.
        clear_first: If True, delete all existing categories before seeding.

    Returns:
        Dict with counts: created, updated, skipped, deactivated.
    """
    raw_data = _load_taxonomy_data()
    flat_categories = _flatten_taxonomy(raw_data)

    counts = {"created": 0, "updated": 0, "skipped": 0, "deactivated": 0}

    # Build a set of all IDs for deactivation check
    taxonomy_ids = {c["id"] for c in flat_categories}

    # Optionally clear existing categories first
    if clear_first and not dry_run:
        # Use raw SQL to delete all categories (more reliable than ORM bulk delete)
        from sqlalchemy import text
        result = db.execute(text("DELETE FROM categories"))
        print(f"DEBUG: Deleted {result.rowcount} categories via raw SQL")
        db.flush()
        
        # Verify deletion
        remaining = db.query(Category).count()
        print(f"DEBUG: Categories remaining after delete: {remaining}")

    for cat_data in flat_categories:
        cat_id = cat_data["id"]
        slug = cat_data["slug"]

        # Check if category already exists (by ID or slug)
        existing = db.query(Category).filter(
            (Category.id == cat_id) | (Category.slug == slug)
        ).first()

        if existing:
            # Update if changed
            changed = False
            for key, value in cat_data.items():
                if key == "id":
                    continue
                current = getattr(existing, key, None)
                if current != value:
                    setattr(existing, key, value)
                    changed = True

            if changed and not dry_run:
                counts["updated"] += 1
            else:
                counts["skipped"] += 1
        else:
            if not dry_run:
                category = Category(**cat_data)
                if country_code:
                    category.country_code = country_code
                db.add(category)
            counts["created"] += 1

    if not dry_run:
        db.flush()
        # Rebuild materialized paths
        rebuild_category_paths(db)

    # Deactivate categories not in taxonomy
    if deactivate_missing and not dry_run:
        missing = db.query(Category).filter(
            ~Category.id.in_(taxonomy_ids),
            Category.is_active.is_(True),
        ).all()
        for cat in missing:
            cat.is_active = False
            counts["deactivated"] += 1
        db.flush()

    if not dry_run:
        db.commit()

    return counts


def main():
    parser = argparse.ArgumentParser(description="Seed comprehensive category taxonomy")
    parser.add_argument("--country", type=str, default=None, help="ISO country code (e.g., AE). If omitted, categories are global (NULL country_code)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--deactivate", action="store_true", help="Deactivate categories not in taxonomy")
    parser.add_argument("--clear", action="store_true", help="Delete all existing categories before seeding")
    args = parser.parse_args()

    db = next(get_db())
    try:
        # Debug: check current state
        existing_count = db.query(Category).count()
        print(f"DEBUG: Existing categories before seed: {existing_count}")
        
        counts = seed_categories(
            db,
            country_code=args.country,
            dry_run=args.dry_run,
            deactivate_missing=args.deactivate,
            clear_first=args.clear,
        )
        action = "Would process" if args.dry_run else "Processed"
        print(f"{action}: {counts['created']} created, {counts['updated']} updated, "
              f"{counts['skipped']} skipped, {counts['deactivated']} deactivated")
    finally:
        db.close()


if __name__ == "__main__":
    main()
