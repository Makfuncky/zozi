from __future__ import annotations

"""Category Attribute Schema Service (Layer 3).

Manages category-specific attribute schemas stored as JSONB.
Enables dynamic form generation and category-specific product validation.

The schema format:
{
    "attributes": [
        {
            "key": "brand",
            "label": "Brand",
            "type": "string",       // string, number, boolean, enum, multi_select
            "required": true,
            "filterable": true,     // show in search filters
            "options": [],           // for enum/multi_select types
            "placeholder": "Enter brand name",
            "validation": {"min": 1, "max": 100}
        }
    ]
}
"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from domains.catalog.models.products import Category

logger = logging.getLogger(__name__)

# ── Default schemas for common categories ──────────────────────────────────
# These provide sensible defaults when a category has no explicit schema.

_DEFAULT_SCHEMAS: Dict[int, Dict[str, Any]] = {
    # Electronics - Mobile Phones
    10101: {
        "attributes": [
            {"key": "brand", "label": "Brand", "type": "string", "required": True, "filterable": True},
            {"key": "model", "label": "Model", "type": "string", "required": True, "filterable": True},
            {"key": "storage", "label": "Storage (GB)", "type": "enum", "required": False, "filterable": True,
             "options": ["32", "64", "128", "256", "512", "1024"]},
            {"key": "ram", "label": "RAM (GB)", "type": "enum", "required": False, "filterable": True,
             "options": ["2", "3", "4", "6", "8", "12", "16"]},
            {"key": "color", "label": "Color", "type": "string", "required": False, "filterable": True},
            {"key": "screen_size", "label": "Screen Size", "type": "string", "required": False},
            {"key": "battery_capacity", "label": "Battery (mAh)", "type": "number", "required": False},
            {"key": "warranty_months", "label": "Warranty (months)", "type": "number", "required": False},
        ]
    },
    # Electronics - Laptops
    10201: {
        "attributes": [
            {"key": "brand", "label": "Brand", "type": "string", "required": True, "filterable": True},
            {"key": "processor", "label": "Processor", "type": "string", "required": True, "filterable": True},
            {"key": "ram", "label": "RAM (GB)", "type": "enum", "required": True, "filterable": True,
             "options": ["4", "8", "16", "32", "64"]},
            {"key": "storage", "label": "Storage", "type": "enum", "required": True, "filterable": True,
             "options": ["128GB SSD", "256GB SSD", "512GB SSD", "1TB SSD", "2TB SSD"]},
            {"key": "graphics", "label": "Graphics Card", "type": "string", "required": False, "filterable": True},
            {"key": "screen_size", "label": "Screen Size", "type": "enum", "required": False, "filterable": True,
             "options": ["13\"", "14\"", "15.6\"", "16\"", "17\""]},
        ]
    },
    # Fashion - Women's Dresses
    20101: {
        "attributes": [
            {"key": "size", "label": "Size", "type": "multi_select", "required": True, "filterable": True,
             "options": ["XS", "S", "M", "L", "XL", "XXL"]},
            {"key": "color", "label": "Color", "type": "string", "required": True, "filterable": True},
            {"key": "material", "label": "Material", "type": "string", "required": False, "filterable": True},
            {"key": "occasion", "label": "Occasion", "type": "enum", "required": False, "filterable": True,
             "options": ["Casual", "Formal", "Party", "Wedding", "Beach"]},
            {"key": "length", "label": "Dress Length", "type": "enum", "required": False, "filterable": True,
             "options": ["Mini", "Knee", "Midi", "Maxi"]},
            {"key": "sleeve", "label": "Sleeve Type", "type": "enum", "required": False,
             "options": ["Sleeveless", "Short", "3/4", "Long"]},
        ]
    },
    # Fashion - Men's Shirts
    20201: {
        "attributes": [
            {"key": "size", "label": "Size", "type": "multi_select", "required": True, "filterable": True,
             "options": ["XS", "S", "M", "L", "XL", "XXL", "3XL"]},
            {"key": "color", "label": "Color", "type": "string", "required": True, "filterable": True},
            {"key": "material", "label": "Material", "type": "string", "required": False, "filterable": True},
            {"key": "fit", "label": "Fit Type", "type": "enum", "required": False, "filterable": True,
             "options": ["Slim", "Regular", "Relaxed", "Oversized"]},
            {"key": "collar", "label": "Collar Type", "type": "enum", "required": False,
             "options": ["Button-Down", "Spread", "Mandarin", "Club"]},
        ]
    },
    # Footwear - Sneakers
    20403: {
        "attributes": [
            {"key": "size", "label": "Size (EU)", "type": "multi_select", "required": True, "filterable": True,
             "options": ["36", "37", "38", "39", "40", "41", "42", "43", "44", "45"]},
            {"key": "color", "label": "Color", "type": "string", "required": True, "filterable": True},
            {"key": "brand", "label": "Brand", "type": "string", "required": True, "filterable": True},
            {"key": "gender", "label": "Gender", "type": "enum", "required": False, "filterable": True,
             "options": ["Men", "Women", "Unisex"]},
            {"key": "material", "label": "Upper Material", "type": "string", "required": False},
        ]
    },
    # Beauty - Skincare
    40101: {
        "attributes": [
            {"key": "brand", "label": "Brand", "type": "string", "required": True, "filterable": True},
            {"key": "skin_type", "label": "Skin Type", "type": "multi_select", "required": True, "filterable": True,
             "options": ["Normal", "Dry", "Oily", "Combination", "Sensitive"]},
            {"key": "volume", "label": "Volume", "type": "string", "required": False, "filterable": True},
            {"key": "spf", "label": "SPF", "type": "enum", "required": False, "filterable": True,
             "options": ["SPF 15", "SPF 30", "SPF 50", "SPF 50+"]},
            {"key": "concern", "label": "Skin Concern", "type": "multi_select", "required": False,
             "options": ["Acne", "Aging", "Dark Spots", "Dryness", "Oiliness", "Pores"]},
        ]
    },
}


# ── Service Functions ───────────────────────────────────────────────────────


def get_attribute_schema(
    db: Session,
    category_id: int,
) -> Optional[Dict[str, Any]]:
    """Get the attribute schema for a category.

    Returns the explicit schema if set, otherwise falls back to the
    default schema for the category, then its ancestors.
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        return None

    # If this category has an explicit schema, use it
    explicit = getattr(category, "attribute_schema", None)
    if explicit:
        return explicit

    # Fall back to default schema
    if category_id in _DEFAULT_SCHEMAS:
        return _DEFAULT_SCHEMAS[category_id]

    # Fall back to ancestor's default schema
    if category.path:
        # Parse path like "/1/15/42/" to get ancestor IDs (exclude self)
        ancestor_ids = [int(x) for x in category.path.strip("/").split("/") if x]
        ancestor_ids = [aid for aid in ancestor_ids if aid != category_id]
        for anc_id in reversed(ancestor_ids):
            if anc_id in _DEFAULT_SCHEMAS:
                return _DEFAULT_SCHEMAS[anc_id]

    return None


def set_attribute_schema(
    db: Session,
    category_id: int,
    schema: Dict[str, Any],
) -> bool:
    """Set the attribute schema for a category.

    Args:
        db: Database session.
        category_id: Category ID.
        schema: Schema dict with "attributes" key.

    Returns:
        True if successful, False if category not found or invalid schema.
    """
    # Validate schema format
    if not isinstance(schema, dict):
        return False
    if "attributes" not in schema:
        return False
    if not isinstance(schema["attributes"], list):
        return False

    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        return False

    category.attribute_schema = schema
    db.commit()
    logger.info("category.attribute_schema.updated id=%s", category_id)
    return True


def validate_product_attributes(
    db: Session,
    category_id: int,
    attributes: Dict[str, Any],
) -> List[str]:
    """Validate product attributes against the category schema.

    Args:
        db: Database session.
        category_id: Category ID.
        attributes: Product attributes to validate.

    Returns:
        List of validation error messages (empty if valid).
    """
    schema = get_attribute_schema(db, category_id)
    if schema is None:
        return []  # No schema means no validation

    errors: List[str] = []
    schema_attrs = schema.get("attributes", [])
    schema_keys = {a["key"]: a for a in schema_attrs}

    # Check required fields
    for attr_def in schema_attrs:
        if attr_def.get("required") and attr_def["key"] not in attributes:
            errors.append(f"Missing required attribute: {attr_def.get('label', attr_def['key'])}")

    # Validate provided attributes
    for key, value in attributes.items():
        if key not in schema_keys:
            continue  # Extra attributes are allowed
        attr_def = schema_keys[key]
        attr_type = attr_def.get("type", "string")

        if attr_type == "number":
            try:
                float(value)
            except (ValueError, TypeError):
                errors.append(f"{attr_def.get('label', key)} must be a number")

        elif attr_type == "boolean":
            if not isinstance(value, bool):
                errors.append(f"{attr_def.get('label', key)} must be a boolean")

        elif attr_type == "enum":
            options = attr_def.get("options", [])
            if options and value not in options:
                errors.append(f"{attr_def.get('label', key)} must be one of: {', '.join(options)}")

        elif attr_type == "multi_select":
            options = attr_def.get("options", [])
            if isinstance(value, list):
                invalid = [v for v in value if v not in options]
                if invalid:
                    errors.append(f"Invalid options for {attr_def.get('label', key)}: {', '.join(invalid)}")

    return errors


def get_filterable_attributes(
    db: Session,
    category_id: int,
) -> List[Dict[str, Any]]:
    """Get only the filterable attributes for search/filter UI."""
    schema = get_attribute_schema(db, category_id)
    if schema is None:
        return []

    return [
        attr for attr in schema.get("attributes", [])
        if attr.get("filterable")
    ]


def list_default_schemas() -> Dict[int, Dict[str, Any]]:
    """Return all default schemas (for admin reference)."""
    return dict(_DEFAULT_SCHEMAS)
