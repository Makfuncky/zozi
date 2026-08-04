"""Permissions write service — DB write operations for permission entities."""

from typing import Optional

from sqlalchemy.orm import Session

from data.models import RolePermissionSetting


def get_all_role_permission_settings(db: Session) -> list[RolePermissionSetting]:
    """Return all persisted role-permission settings."""
    return db.query(RolePermissionSetting).all()


def get_role_permission_setting(db: Session, role: str) -> Optional[RolePermissionSetting]:
    """Return the persisted permission setting for *role* or None."""
    return db.query(RolePermissionSetting).filter(RolePermissionSetting.role == role).first()


def upsert_role_permission_setting(
    db: Session,
    role: str,
    permissions_json: list[str],
    updated_by_id: int | None = None,
) -> RolePermissionSetting:
    row = db.query(RolePermissionSetting).filter(RolePermissionSetting.role == role).first()
    if row is None:
        row = RolePermissionSetting(
            role=role,
            permissions_json=permissions_json,
            updated_by_id=updated_by_id,
        )
        db.add(row)
    else:
        row.permissions_json = permissions_json
        row.updated_by_id = updated_by_id
    db.commit()
    db.refresh(row)
    return row