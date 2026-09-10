"""Admin permissions router — exposes the security permission matrix at /permissions/*.

The /admin/permissions Next.js page calls:
  GET   /permissions/categories                  — list permission categories with permissions
  POST  /permissions/categories                  — create category
  DELETE /permissions/categories/{id}            — soft-delete category
  GET   /permissions/list                        — flat list of all permissions
  GET   /permissions/roles/{role}                — get role's granted permissions
  POST  /permissions/roles/assign                — assign permission to role
  POST  /permissions/roles/revoke                — revoke permission from role
  POST  /permissions/users/override              — set user-level permission override

These delegate to rbac.services.permissions_service (already implemented).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from rbac.dependencies import require_feature

router = APIRouter(tags=["admin", "permissions"])


def _current_admin_id(current_user: dict) -> int:
    try:
        return int(current_user.get("id") or 0)
    except (TypeError, ValueError):
        return 0


@router.get("/permissions/categories", status_code=200)
def list_permission_categories_route(
    country_code: Optional[str] = Query(None),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.permissions.manage")),
):
    """List permission categories with their permissions embedded.

    Returns a list of dicts shaped like:
      {
        "id": int,
        "name": str,
        "slug": str,
        "description": str | None,
        "icon": str | None,
        "sort_order": int,
        "is_active": bool,
        "permissions_count": int,
        "permissions": [Permission, ...]
      }
    """
    from rbac.services.permissions_service import list_categories, list_permissions

    cats = list_categories(db, country_code=country_code)
    perms = list_permissions(db, country_code=country_code)

    by_cat: dict[int, list[dict]] = {}
    for perm in perms:
        by_cat.setdefault(perm.get("category_id"), []).append(perm)

    out = []
    for cat in cats:
        items = by_cat.get(cat.get("id"), [])
        out.append({
            "id": cat["id"],
            "name": cat["name"],
            "slug": cat["slug"],
            "description": cat.get("description"),
            "icon": cat.get("icon"),
            "sort_order": cat.get("sort_order", 0),
            "is_active": bool(cat.get("is_active", True)),
            "permissions_count": len(items),
            "permissions": [
                {
                    "id": p["id"],
                    "category_id": p["category_id"],
                    "name": p["name"],
                    "slug": p["slug"],
                    "description": p.get("description"),
                    "scope": p.get("scope", "global"),
                    "is_active": bool(p.get("is_active", True)),
                }
                for p in items
            ],
        })
    return out


@router.post("/permissions/categories", status_code=201)
def create_permission_category_route(
    body: dict = Body(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.permissions.manage")),
):
    """Create a new permission category."""
    from rbac.services.permissions_service import create_category

    name = (body.get("name") or "").strip()
    if not name:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="name is required")

    payload = {
        "name": name,
        "slug": (body.get("slug") or name.lower().replace(" ", "-")).strip(),
        "description": body.get("description"),
        "icon": body.get("icon"),
        "sort_order": int(body.get("sort_order") or 0),
        "is_active": bool(body.get("is_active", True)),
        "country_code": body.get("country_code"),
    }
    actor_id = _current_admin_id(current_user)
    return create_category(db, payload, actor_id)


@router.delete("/permissions/categories/{category_id}", status_code=200)
def delete_permission_category_route(
    category_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.permissions.manage")),
):
    """Soft-delete a permission category (writes audit log)."""
    from rbac.services.permissions_service import delete_category

    actor_id = _current_admin_id(current_user)
    return delete_category(db, category_id, actor_id)


@router.get("/permissions/list", status_code=200)
def list_permissions_route(
    country_code: Optional[str] = Query(None),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.permissions.manage")),
):
    """Flat list of all permissions with their category."""
    from rbac.services.permissions_service import list_permissions

    rows = list_permissions(db, country_code=country_code)
    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "name": r["name"],
            "slug": r["slug"],
            "description": r.get("description"),
            "scope": r.get("scope", "global"),
            "is_active": bool(r.get("is_active", True)),
            "category_id": r.get("category_id"),
            "category_name": r.get("category_name"),
            "category_slug": r.get("category_slug"),
        })
    return out


@router.get("/permissions/roles/{role}", status_code=200)
def get_role_permissions_route(
    role: str,
    country_code: Optional[str] = Query(None),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.permissions.manage")),
):
    """Get all permissions granted to a role (keyed by slug).

    Returns: { "<permission_slug>": {"granted": true, "permission_id": int, "name": str}, ... }
    """
    from rbac.services.permissions_service import get_role_permissions

    rows = get_role_permissions(db, role, country_code=country_code)
    result: dict[str, dict] = {}
    for row in rows:
        slug = row.get("permission_slug")
        if not slug:
            continue
        result[slug] = {
            "granted": True,
            "permission_id": row.get("permission_id"),
            "name": row.get("permission_name"),
        }
    return result


@router.post("/permissions/roles/assign", status_code=200)
def assign_role_permission_route(
    body: dict = Body(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.permissions.manage")),
):
    """Assign a single permission to a role."""
    from rbac.services.permissions_service import get_role_permissions

    role = body.get("role_name") or body.get("role")
    pid = body.get("permission_id")
    if not role or pid is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="role_name and permission_id are required")

    actor_id = _current_admin_id(current_user)
    country_code = body.get("country_code")
    from rbac.services.permissions_service import set_role_permissions
    current_rows = get_role_permissions(db, role, country_code=country_code)
    current_ids = sorted({int(r["permission_id"]) for r in current_rows})
    if int(pid) not in current_ids:
        current_ids.append(int(pid))
    return set_role_permissions(db, role, current_ids, country_code, actor_id)


@router.post("/permissions/roles/revoke", status_code=200)
def revoke_role_permission_route(
    body: dict = Body(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.permissions.manage")),
):
    """Revoke a single permission from a role."""
    from rbac.services.permissions_service import get_role_permissions, set_role_permissions

    role = body.get("role_name") or body.get("role")
    pid = body.get("permission_id")
    if not role or pid is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="role_name and permission_id are required")

    actor_id = _current_admin_id(current_user)
    country_code = body.get("country_code")
    current_rows = get_role_permissions(db, role, country_code=country_code)
    current_ids = sorted({int(r["permission_id"]) for r in current_rows if int(r["permission_id"]) != int(pid)})
    return set_role_permissions(db, role, current_ids, country_code, actor_id)


@router.post("/permissions/users/override", status_code=200)
def set_user_permission_override_route(
    body: dict = Body(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.permissions.manage")),
):
    """Set a per-user permission override (granted or revoked)."""
    from rbac.services.permissions_service import set_user_override

    user_id = body.get("user_id")
    pid = body.get("permission_id")
    granted = body.get("is_granted")
    if user_id is None or pid is None or granted is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="user_id, permission_id, is_granted are required")

    actor_id = _current_admin_id(current_user)
    country_code = body.get("country_code")
    return set_user_override(db, int(user_id), int(pid), bool(granted), country_code, actor_id)
