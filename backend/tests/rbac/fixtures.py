"""Shared RBAC seed helpers for tests."""
from __future__ import annotations

from sqlalchemy import text


_RBAC_SEED_CATEGORIES = [
    {
        "id": 1,
        "name": "General",
        "slug": "general",
        "description": "General-purpose permissions",
        "icon": "general",
        "sort_order": 0,
        "is_active": True,
        "country_code": "OM",
    },
]


def seed_permission_categories(session) -> None:
    """Idempotently insert the RBAC permission categories required by tests.

    ``rbac/service.py`` hardcodes ``category_id=1`` in
    ``_get_or_create_permission``; without a matching
    ``permission_categories`` row every INSERT into ``permissions`` fails
    with an FK IntegrityError.
    """
    for cat in _RBAC_SEED_CATEGORIES:
        row = session.execute(
            text("SELECT id FROM permission_categories WHERE id = :id"),
            {"id": cat["id"]},
        ).fetchone()
        if not row:
            from rbac.models.permission_entities import PermissionCategory
            session.add(PermissionCategory(**cat))
