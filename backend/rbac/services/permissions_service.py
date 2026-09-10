"""RBAC permission service — small admin-side CRUD for the permission matrix.

Used by the /admin/permissions UI. Returns plain dicts (Law 2: routers stay
thin and never serialize models directly). All mutating operations write a
row to ``permission_audit_log`` for traceability.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def list_categories(db: Session, country_code: Optional[str] = None) -> list[dict]:
    params: dict[str, Any] = {}
    where = "WHERE is_deleted = FALSE"
    if country_code:
        where += " AND country_code = :cc"
        params["cc"] = country_code.upper()
    rows = db.execute(
        text(
            f"""
            SELECT id, name, slug, description, icon, sort_order, is_active,
                   country_code, created_at, updated_at
            FROM security.permission_categories
            {where}
            ORDER BY sort_order, name
            """
        ),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]


def create_category(db: Session, payload: dict, actor_id: int) -> dict:
    row = db.execute(
        text(
            """
            INSERT INTO security.permission_categories
                (name, slug, description, icon, sort_order, is_active,
                 country_code, created_at, updated_at, created_by, updated_by)
            VALUES
                (:name, :slug, :description, :icon, :sort_order, :is_active,
                 :country_code, NOW(), NOW(), :actor, :actor)
            RETURNING id
            """
        ),
        {
            "name": payload.get("name"),
            "slug": payload.get("slug"),
            "description": payload.get("description"),
            "icon": payload.get("icon"),
            "sort_order": int(payload.get("sort_order") or 0),
            "is_active": bool(payload.get("is_active", True)),
            "country_code": (payload.get("country_code") or "OM").upper(),
            "actor": actor_id,
        },
    ).mappings().first()
    db.commit()
    return {"id": row["id"], "status": "created"}


def delete_category(db: Session, category_id: int, actor_id: int) -> dict:
    db.execute(
        text(
            """
            UPDATE security.permission_categories
            SET is_deleted = TRUE, deleted_at = NOW(), deleted_by = :actor,
                updated_at = NOW(), updated_by = :actor
            WHERE id = :id AND is_deleted = FALSE
            """
        ),
        {"id": category_id, "actor": actor_id},
    )
    db.execute(
        text(
            """
            INSERT INTO security.permission_audit_log
                (actor_id, action, target_role, details, country_code, created_at)
            VALUES
                (:actor, 'delete_category', NULL, :details, NULL, NOW())
            """
        ),
        {"actor": actor_id, "details": f"Deleted permission category {category_id}"},
    )
    db.commit()
    return {"id": category_id, "status": "deleted"}


def list_permissions(db: Session, country_code: Optional[str] = None) -> list[dict]:
    params: dict[str, Any] = {}
    where = "WHERE p.is_deleted = FALSE"
    if country_code:
        where += " AND p.country_code = :cc"
        params["cc"] = country_code.upper()
    rows = db.execute(
        text(
            f"""
            SELECT p.id, p.name, p.slug, p.description, p.scope, p.is_active,
                   p.country_code, p.category_id, c.name AS category_name,
                   c.slug AS category_slug
            FROM security.permissions p
            LEFT JOIN security.permission_categories c ON c.id = p.category_id
            {where}
            ORDER BY c.sort_order, c.name, p.name
            """
        ),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]


def get_role_permissions(db: Session, role: str, country_code: Optional[str] = None) -> list[dict]:
    params: dict[str, Any] = {"role": role}
    where = "WHERE rpa.role_name = :role AND rpa.is_granted = TRUE"
    if country_code:
        where += " AND (rpa.country_code = :cc OR rpa.country_code IS NULL)"
        params["cc"] = country_code.upper()
    rows = db.execute(
        text(
            f"""
            SELECT rpa.id, rpa.role_name, rpa.permission_id, rpa.country_code,
                   p.name AS permission_name, p.slug AS permission_slug,
                   p.scope, p.category_id, c.name AS category_name
            FROM security.role_permission_assignments rpa
            JOIN security.permissions p ON p.id = rpa.permission_id
            LEFT JOIN security.permission_categories c ON c.id = p.category_id
            {where}
            ORDER BY c.name, p.name
            """
        ),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]


def set_role_permissions(
    db: Session,
    role: str,
    permission_ids: Iterable[int],
    country_code: Optional[str],
    actor_id: int,
) -> dict:
    """Replace the set of permissions granted to ``role`` for ``country_code``.

    Removes existing grants for the country (or all countries when
    ``country_code`` is ``None``) and re-inserts the supplied ids. The
    resulting state is always exactly the supplied set.
    """
    cc = (country_code or "").upper() or None
    if cc is None:
        db.execute(
            text("DELETE FROM security.role_permission_assignments WHERE role_name = :role"),
            {"role": role},
        )
    else:
        db.execute(
            text(
                """
                DELETE FROM security.role_permission_assignments
                WHERE role_name = :role AND country_code = :cc
                """
            ),
            {"role": role, "cc": cc},
        )
    inserted = 0
    for pid in permission_ids:
        db.execute(
            text(
                """
                INSERT INTO security.role_permission_assignments
                    (role_name, permission_id, country_code, granted_by, is_granted,
                     created_at, updated_at)
                VALUES
                    (:role, :pid, :cc, :actor, TRUE, NOW(), NOW())
                """
            ),
            {"role": role, "pid": int(pid), "cc": cc, "actor": actor_id},
        )
        inserted += 1
    db.execute(
        text(
            """
            INSERT INTO security.permission_audit_log
                (actor_id, action, target_role, details, country_code, created_at)
            VALUES
                (:actor, 'set_role_permissions', :role, :details, :cc, NOW())
            """
        ),
        {
            "actor": actor_id,
            "role": role,
            "cc": cc,
            "details": f"Granted {inserted} permissions to {role}",
        },
    )
    db.commit()
    return {"role": role, "country_code": cc, "granted": inserted}


def set_user_override(
    db: Session,
    user_id: int,
    permission_id: int,
    is_granted: bool,
    country_code: Optional[str],
    actor_id: int,
) -> dict:
    cc = (country_code or "").upper() or None
    db.execute(
        text(
            """
            INSERT INTO security.user_permission_overrides
                (user_id, permission_id, country_code, is_granted, granted_by,
                 created_at, updated_at)
            VALUES
                (:uid, :pid, :cc, :granted, :actor, NOW(), NOW())
            ON CONFLICT (user_id, permission_id, country_code)
            DO UPDATE SET is_granted = EXCLUDED.is_granted,
                          granted_by = EXCLUDED.granted_by,
                          updated_at = NOW()
            """
        ),
        {
            "uid": user_id,
            "pid": int(permission_id),
            "cc": cc,
            "granted": bool(is_granted),
            "actor": actor_id,
        },
    )
    db.execute(
        text(
            """
            INSERT INTO security.permission_audit_log
                (actor_id, action, target_user_id, permission_id, country_code, created_at)
            VALUES
                (:actor, 'user_permission_override', :uid, :pid, :cc, NOW())
            """
        ),
        {
            "actor": actor_id,
            "uid": user_id,
            "pid": int(permission_id),
            "cc": cc,
        },
    )
    db.commit()
    return {
        "user_id": user_id,
        "permission_id": int(permission_id),
        "is_granted": bool(is_granted),
        "country_code": cc,
    }
