"""Admin permissions management controller."""
from __future__ import annotations

import json
from typing import Any, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import RolePermissionSetting
from utils.staff_permissions import (
    DEFAULT_ROLE_PERMISSION_MAP,
    KNOWN_ROLE_PERMISSIONS,
    default_permissions_for_role,
)
from .analytics import ROLE_PERMISSION_MAP

from services.write_helpers import add_and_flush, commit_only

STAFF_PERMISSION_GROUPS = [
    {"key": "orders", "label": "Order Management", "permissions": ("orders.manage", "orders.view", "orders.cancel")},
    {"key": "products", "label": "Product Management", "permissions": ("products.manage", "products.view", "products.approve")},
]


def get_staff_permission_catalog() -> dict[str, Any]:
    return {
        "groups": [
            {
                "key": cast(str, group["key"]),
                "label": cast(str, group["label"]),
                "permissions": list(cast(tuple[str, ...], group["permissions"])),
            }
            for group in STAFF_PERMISSION_GROUPS
        ],
        "defaults": {
            role: default_permissions_for_role(role)
            for role in sorted(DEFAULT_ROLE_PERMISSION_MAP.keys())
        },
    }


def load_role_permission_settings(db: Session) -> dict[str, set[str]]:
    """Reload the runtime role-permission matrix from persisted DB overrides."""
    next_map = {
        role: set(permissions)
        for role, permissions in DEFAULT_ROLE_PERMISSION_MAP.items()
    }
    rows = db.query(RolePermissionSetting).all()
    for row in rows:
        role = cast(str | None, getattr(row, "role", None))
        if role not in next_map:
            continue

        raw_permissions = getattr(row, "permissions_json", None)
        if isinstance(raw_permissions, str):
            serialized_permissions = raw_permissions.strip()
            if serialized_permissions:
                try:
                    raw_permissions = json.loads(serialized_permissions)
                except (TypeError, ValueError, json.JSONDecodeError):
                    raw_permissions = [item.strip() for item in serialized_permissions.split(",")]
            else:
                raw_permissions = []
        if isinstance(raw_permissions, dict):
            raw_permissions = raw_permissions.get("permissions", [])
        if isinstance(raw_permissions, list):
            next_map[role] = {
                str(permission).strip()
                for permission in raw_permissions
                if str(permission).strip() in KNOWN_ROLE_PERMISSIONS
            }
            continue

    ROLE_PERMISSION_MAP.clear()
    ROLE_PERMISSION_MAP.update(next_map)
    return ROLE_PERMISSION_MAP


def get_hierarchy_permissions(current_user: dict) -> dict:
    role = cast(str | None, current_user["role"])
    return {
        "role": role,
        "permissions": sorted(ROLE_PERMISSION_MAP.get(role, set())) if role else [],
        "matrix": {k: sorted(v) for k, v in ROLE_PERMISSION_MAP.items()},
    }


def update_role_permissions(role: str, new_permissions: list[str], db: Session, current_user: dict) -> dict:
    """Persist a new permission set for *role* and update the in-memory map.

    Only admin users may call this endpoint.  The supplied permissions are
    validated against the full set of known permission strings so that typos
    are caught early.
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin-only access required")

    if role not in ROLE_PERMISSION_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown role: {role}")

    unknown = [p for p in new_permissions if p not in KNOWN_ROLE_PERMISSIONS]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown permission(s): {', '.join(sorted(unknown))}",
        )

    # Upsert the DB row
    row = db.query(RolePermissionSetting).filter(RolePermissionSetting.role == role).first()
    if row is None:
        row = RolePermissionSetting(
            role=role,
            permissions_json=new_permissions,
            updated_by_id=current_user["id"],
        )
        add_and_flush(db, row)
    else:
        row.permissions_json = new_permissions
        row.updated_by_id = current_user["id"]
    commit_only(db)

    load_role_permission_settings(db)

    return {
        "role": role,
        "permissions": sorted(new_permissions),
        "matrix": {k: sorted(v) for k, v in ROLE_PERMISSION_MAP.items()},
    }
