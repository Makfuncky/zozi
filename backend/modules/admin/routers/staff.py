"""Admin staff router — thin proxy at /admin/staff matching frontend paths.

The /admin/staff Next.js page calls:
  GET  /admin/staff                — list all staff
  POST /admin/staff                — create new staff
  PUT  /admin/staff/{user_id}      — update staff
  DELETE /admin/staff/{user_id}    — delete staff
  PUT  /admin/staff/bulk           — bulk update staff
  GET  /admin/staff/permission-catalog — permission catalog for staff
  POST /admin/users/{user_id}/reset-password — used by staff reset-password UI

These map to the same service-layer operations as /api/v1/admin/accounts/staff
but with the simpler /admin/staff/* path the frontend uses.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session

from domains.accounts.services.users.user_management_service import (
    list_staff_accounts,
    create_staff_account,
    update_staff_account,
    delete_staff_account,
    bulk_update_staff_accounts,
)
from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from infrastructure.database.schemas import (
    CreateStaffAccount,
    UpdateStaffAccount,
    BulkUpdateStaffBody,
)
from rbac.dependencies import require_feature

router = APIRouter(tags=["admin", "staff"])


@router.get("/admin/staff", status_code=200)
def list_staff_route(
    role: Optional[str] = Query(None, description="Filter by role (admin, sub_admin, moderator, support)"),
    status: Optional[str] = Query(None, description="Filter by active status: active|inactive"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.user.list")),
):
    """List staff accounts (admin, sub_admin, moderator, support)."""
    items = list_staff_accounts(db)
    if role:
        items = [u for u in items if (u.get("role") or "").lower() == role.lower()]
    if status:
        if status.lower() == "active":
            items = [u for u in items if u.get("is_active")]
        elif status.lower() == "inactive":
            items = [u for u in items if not u.get("is_active")]
    return items


@router.post("/admin/staff", status_code=201)
def create_staff_route(
    payload: CreateStaffAccount,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.user.create")),
):
    """Create a new staff account."""
    return create_staff_account(payload, current_user, db)


@router.put("/admin/staff/{user_id}", status_code=200)
def update_staff_route(
    user_id: int,
    payload: UpdateStaffAccount,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.user.update")),
):
    """Update an existing staff account."""
    return update_staff_account(user_id, payload, current_user, db)


@router.patch("/admin/staff/{user_id}", status_code=200)
def patch_staff_route(
    user_id: int,
    payload: UpdateStaffAccount,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.user.update")),
):
    """Partial update for a staff account (used by status toggle)."""
    return update_staff_account(user_id, payload, current_user, db)


@router.delete("/admin/staff/{user_id}", status_code=200)
def delete_staff_route(
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.user.delete")),
):
    """Delete a staff account."""
    return delete_staff_account(user_id, current_user, db)


@router.put("/admin/staff/bulk", status_code=200)
def bulk_update_staff_route(
    body: BulkUpdateStaffBody,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.user.update")),
):
    """Bulk update multiple staff accounts."""
    return bulk_update_staff_accounts(body.user_ids, body.updates, current_user, db)


@router.get("/admin/staff/permission-catalog", status_code=200)
def staff_permission_catalog_route(
    current_user: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("accounts.permissions.manage")),
):
    """Permission catalog for the staff management UI.

    Returns the canonical StaffPermissionGroup list + role defaults so the
    frontend can populate the permission matrix without hardcoding.
    """
    from rbac.catalog import FEATURE_CATALOG

    groups = [
        {
            "key": "governance",
            "label": "Governance",
            "permissions": ["analytics.view", "audit.read", "hierarchy.view"],
        },
        {
            "key": "users",
            "label": "Users & Staff",
            "permissions": [
                "users.read",
                "users.role.update",
                "users.toggle_active",
                "users.delete",
                "users.reset_password",
                "staff.view",
                "staff.create",
                "staff.manage",
                "staff.delete",
            ],
        },
        {
            "key": "commerce",
            "label": "Commerce Operations",
            "permissions": [
                "orders.manage",
                "products.manage",
                "moderation.suppliers",
                "moderation.products",
                "tickets.manage",
                "coupons.manage",
                "payouts.verify",
            ],
        },
        {
            "key": "countries",
            "label": "Country Management",
            "permissions": [
                "countries.configure",
                "countries.payouts",
                "countries.commissions",
                "countries.promotions",
                "countries.finance",
                "countries.banners",
                "countries.email",
            ],
        },
    ]

    known_features = set(FEATURE_CATALOG.keys()) if isinstance(FEATURE_CATALOG, dict) else set()
    for group in groups:
        group["permissions"] = [p for p in group["permissions"] if p in known_features] or group["permissions"]

    defaults = {
        "admin": [p for group in groups for p in group["permissions"]],
        "sub_admin": [
            "analytics.view",
            "users.read",
            "users.toggle_active",
            "orders.manage",
            "products.manage",
            "moderation.products",
            "tickets.manage",
            "audit.read",
        ],
        "moderator": [
            "analytics.view",
            "users.read",
            "moderation.suppliers",
            "moderation.products",
            "tickets.manage",
            "audit.read",
        ],
        "support": [
            "tickets.manage",
            "users.read",
        ],
    }
    return {"groups": groups, "defaults": defaults}


@router.get("/admin/users", status_code=200)
def list_users_for_permission_ui_route(
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.user.list")),
):
    """List users (cross-country) for the permission UI's user-search picker.

    Supports a simple substring search on email / username / full_name.
    Returns a list of {id, email, username, full_name, role} dicts.
    """
    from domains.accounts.models import User
    from sqlalchemy import or_

    query = db.query(User)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.email.ilike(pattern),
                User.username.ilike(pattern),
                User.full_name.ilike(pattern),
            )
        )
    rows = query.order_by(User.id.desc()).limit(limit).all()

    out = []
    for u in rows:
        out.append({
            "id": getattr(u, "id", None),
            "email": getattr(u, "email", None),
            "username": getattr(u, "username", None),
            "full_name": getattr(u, "full_name", None) or getattr(u, "username", None),
            "role": getattr(u, "role", None),
            "is_active": bool(getattr(u, "is_active", False)),
        })
    return out


@router.post("/admin/users/{user_id}/reset-password", status_code=200)
def reset_user_password_route(
    user_id: int,
    body: dict = Body(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("accounts.password.reset")),
):
    """Reset a user's password (admin console).

    Body: { "new_password": str }
    Hashes the password then forwards to the existing force_reset_password_admin
    service which writes an audit entry.
    """
    from domains.accounts.services.users.user_management_service import (
        force_reset_password_admin,
    )
    from domains.accounts.services.auth.password_service import hash_password

    new_password = (body.get("new_password") or "").strip()
    if len(new_password) < 8:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="new_password must be at least 8 characters")

    password_hash = hash_password(new_password)
    return force_reset_password_admin(user_id, password_hash, current_user, db)
