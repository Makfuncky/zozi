from __future__ import annotations

"""Bulk Category Import/Export Service (Layer 4).

Provides CSV and JSON import/export for category trees with validation.
Supports creating, updating, and deactivating categories in bulk.
"""
import csv
import io
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from domains.catalog.models.products import Category
from domains.catalog.services.categories.category_service import (
    create_category,
    update_category,
)
from infrastructure.utils.category_tree import rebuild_category_paths

logger = logging.getLogger(__name__)


class BulkCategoryResult:
    """Result of a bulk category operation."""

    def __init__(self):
        self.created: int = 0
        self.updated: int = 0
        self.skipped: int = 0
        self.errors: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "errors": self.errors,
        }


def _validate_row(row: Dict[str, Any], line_num: int) -> List[str]:
    """Validate a single import row. Returns list of error messages."""
    errors: List[str] = []

    name = str(row.get("name", "")).strip()
    if not name:
        errors.append(f"Line {line_num}: 'name' is required")

    slug = str(row.get("slug", "")).strip()
    if not slug:
        errors.append(f"Line {line_num}: 'slug' is required")

    parent_id = row.get("parent_id")
    if parent_id is not None and parent_id != "":
        try:
            int(parent_id)
        except (ValueError, TypeError):
            errors.append(f"Line {line_num}: 'parent_id' must be an integer")

    return errors


def import_categories_json(
    db: Session,
    data: List[Dict[str, Any]],
    *,
    country_code: Optional[str] = None,
    rebuild: bool = True,
) -> BulkCategoryResult:
    """Import categories from a flat JSON list.

    Each dict should have: name, slug, parent_id (optional), sort_order (optional),
    description (optional), icon (optional), image_url (optional), is_active (optional).

    Categories are automatically sorted by hierarchy level (parents before children)
    to avoid FK constraint violations.

    Args:
        db: Database session.
        data: List of category dicts.
        country_code: Optional country scope.
        rebuild: Whether to rebuild materialized paths after import.

    Returns:
        BulkCategoryResult with counts and errors.
    """
    result = BulkCategoryResult()

    # Validate all rows first and check for duplicate slugs
    seen_slugs: Dict[str, int] = {}
    for i, row in enumerate(data, start=2):
        errors = _validate_row(row, i)
        if errors:
            result.errors.extend([{"line": i, "message": e} for e in errors])

        slug = str(row.get("slug", "")).strip()
        if slug and slug in seen_slugs:
            result.errors.append({
                "line": i,
                "message": f"Duplicate slug '{slug}' (also on line {seen_slugs[slug]})",
            })
        elif slug:
            seen_slugs[slug] = i

    # If there are validation errors, return early
    if result.errors:
        return result

    # Sort data so parents come before children (FK constraint safety)
    # Categories with parent_id=None or empty come first, then by parent_id
    sorted_data = sorted(
        data,
        key=lambda r: (
            0 if r.get("parent_id") in (None, "") else 1,
            int(r.get("parent_id", 0) or 0),
        ),
    )

    for i, row in enumerate(sorted_data, start=2):
        name = str(row["name"]).strip()
        slug = str(row["slug"]).strip()
        parent_id = int(row["parent_id"]) if row.get("parent_id") not in (None, "") else None

        # Check for existing category by slug
        existing = db.query(Category).filter(Category.slug == slug).first()

        if existing:
            # Update existing
            updates: Dict[str, Any] = {"name": name}
            if parent_id is not None:
                updates["parent_id"] = parent_id
            for key in ("sort_order", "description", "icon", "image_url", "is_active", "commission_rate"):
                if key in row and row[key] is not None:
                    updates[key] = row[key]

            update_category(db, existing, updates, rebuild_paths=False)
            result.updated += 1
        else:
            # Create new
            payload: Dict[str, Any] = {
                "name": name,
                "slug": slug,
                "parent_id": parent_id,
            }
            for key in ("sort_order", "description", "icon", "image_url", "is_active", "commission_rate"):
                if key in row and row[key] is not None:
                    payload[key] = row[key]
            if country_code:
                payload["country_code"] = country_code

            try:
                create_category(db, payload, rebuild_paths=False)
                result.created += 1
            except ValueError as exc:
                result.errors.append({"line": i, "message": str(exc)})

    if rebuild and (result.created > 0 or result.updated > 0):
        rebuild_category_paths(db)

    db.commit()
    logger.info(
        "category.bulk_import created=%s updated=%s errors=%s",
        result.created, result.updated, len(result.errors),
    )
    return result


def import_categories_csv(
    db: Session,
    csv_content: str,
    *,
    country_code: Optional[str] = None,
    delimiter: str = ",",
) -> BulkCategoryResult:
    """Import categories from CSV content.

    Expected columns: name, slug, parent_id, sort_order, description, icon, image_url, is_active

    Args:
        db: Database session.
        csv_content: CSV string content.
        country_code: Optional country scope.
        delimiter: CSV delimiter (default: comma).

    Returns:
        BulkCategoryResult with counts and errors.
    """
    reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
    data = list(reader)
    return import_categories_json(db, data, country_code=country_code)


def export_categories_json(
    db: Session,
    *,
    country_code: Optional[str] = None,
    include_inactive: bool = False,
    include_deleted: bool = False,
) -> List[Dict[str, Any]]:
    """Export categories as a flat JSON list.

    Args:
        db: Database session.
        country_code: Filter by country (optional).
        include_inactive: Include inactive categories.
        include_deleted: Include soft-deleted categories.

    Returns:
        List of category dicts suitable for JSON serialization.
    """
    query = db.query(Category)

    if country_code:
        query = query.filter(Category.country_code == country_code.upper())
    if not include_inactive:
        query = query.filter(Category.is_active.is_(True))
    if not include_deleted:
        query = query.filter(Category.is_deleted.is_(False))

    categories = query.order_by(Category.sort_order, Category.name).all()

    result = []
    for cat in categories:
        result.append({
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "parent_id": cat.parent_id,
            "sort_order": cat.sort_order,
            "description": cat.description,
            "icon": cat.icon,
            "image_url": cat.image_url,
            "is_active": cat.is_active,
            "is_featured": cat.is_featured,
            "is_deleted": cat.is_deleted,
            "commission_rate": float(cat.commission_rate) if cat.commission_rate else None,
            "country_code": cat.country_code,
            "path": cat.path,
            "depth": cat.depth,
            "attribute_schema": getattr(cat, "attribute_schema", None),
            "created_at": cat.created_at.isoformat() if cat.created_at else None,
            "updated_at": cat.updated_at.isoformat() if cat.updated_at else None,
        })

    return result


def export_categories_csv(
    db: Session,
    *,
    country_code: Optional[str] = None,
    include_inactive: bool = False,
) -> str:
    """Export categories as CSV string.

    Args:
        db: Database session.
        country_code: Filter by country (optional).
        include_inactive: Include inactive categories.

    Returns:
        CSV string with category data.
    """
    data = export_categories_json(
        db,
        country_code=country_code,
        include_inactive=include_inactive,
    )

    if not data:
        return ""

    output = io.StringIO()
    fieldnames = [
        "id", "name", "slug", "parent_id", "sort_order",
        "description", "icon", "image_url", "is_active", "country_code",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(data)

    return output.getvalue()


def validate_import_data(
    data: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Validate import data without writing to database.

    Args:
        data: List of category dicts to validate.

    Returns:
        List of error dicts with line numbers and messages.
    """
    errors: List[Dict[str, Any]] = []
    slugs_seen: Dict[str, int] = {}

    for i, row in enumerate(data, start=2):
        row_errors = _validate_row(row, i)
        if row_errors:
            errors.extend([{"line": i, "message": e} for e in row_errors])

        slug = str(row.get("slug", "")).strip()
        if slug in slugs_seen:
            errors.append({
                "line": i,
                "message": f"Duplicate slug '{slug}' (also on line {slugs_seen[slug]})",
            })
        else:
            slugs_seen[slug] = i

    return errors
