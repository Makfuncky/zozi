from __future__ import annotations

"""
Taxonomy domain service.

Loads bundled category taxonomies from JSON files and flattens them for
ingestion. Lives in domains/catalog/services/ per ARCHITECTURE_DIAGRAM.md
because this is domain business logic (it knows about chart-of-categories
shape and parent/child relationships), not SDK wrapping.
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


__all__ = [
    "get_taxonomy_source",
    "list_taxonomy_sources",
    "import_taxonomy",
    "get_taxonomy_version",
]


_TAXONOMY_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
    ),
    "infrastructure",
    "database",
    "seed_data",
)


def _count_categories(nodes: List[Dict[str, Any]]) -> int:
    """Count total categories in a nested taxonomy."""
    count = len(nodes)
    for node in nodes:
        children = node.get("children", [])
        count += _count_categories(children)
    return count


def _flatten_for_import(
    nodes: List[Dict[str, Any]],
    *,
    parent_id: Optional[int] = None,
    result: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Flatten nested taxonomy for database import."""
    if result is None:
        result = []

    for node in nodes:
        children = node.get("children", [])
        result.append({
            "id": node["id"],
            "name": node["name"],
            "slug": node["slug"],
            "parent_id": parent_id,
            "sort_order": node.get("sort_order", 0),
            "is_active": node.get("is_active", True),
            "icon": node.get("icon"),
            "description": node.get("description"),
            "image_url": node.get("image_url"),
            "is_featured": node.get("is_featured", False),
            "commission_rate": node.get("commission_rate"),
        })
        if children:
            _flatten_for_import(children, parent_id=node["id"], result=result)

    return result


def get_taxonomy_source(source: str) -> Optional[Dict[str, Any]]:
    """Get a taxonomy source by name.

    Args:
        source: Source name ('google', 'eclass', 'builtin', 'full').

    Returns:
        Taxonomy dict with metadata and categories, or None if not found.
    """
    source_map = {
        "full": "categories_full.json",
    }

    filename = source_map.get(source.lower())
    if not filename:
        return None

    filepath = os.path.join(_TAXONOMY_DIR, filename)
    if not os.path.exists(filepath):
        logger.warning("Taxonomy file not found: %s", filepath)
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "name": source.lower(),
            "version": "1.0.0",
            "total_categories": _count_categories(data),
            "categories": data,
        }
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to load taxonomy %s: %s", source, exc)
        return None


def list_taxonomy_sources() -> List[Dict[str, str]]:
    """List available taxonomy sources."""
    sources: List[Dict[str, str]] = []

    for name, filename in [("full", "categories_full.json")]:
        filepath = os.path.join(_TAXONOMY_DIR, filename)
        if os.path.exists(filepath):
            sources.append({
                "name": name,
                "type": "bundled",
                "file": filename,
                "status": "available",
            })

    return sources


def import_taxonomy(source: str) -> Optional[List[Dict[str, Any]]]:
    """Import a taxonomy as a flat list of category dicts.

    Args:
        source: Source name ('full', 'google', 'eclass').

    Returns:
        Flat list of category dicts, or None if source not found.
    """
    taxonomy = get_taxonomy_source(source)
    if taxonomy is None:
        return None

    categories = taxonomy.get("categories", [])
    return _flatten_for_import(categories)


def get_taxonomy_version(source: str) -> Optional[str]:
    """Get the version of a taxonomy source."""
    taxonomy = get_taxonomy_source(source)
    if taxonomy is None:
        return None
    return taxonomy.get("version")