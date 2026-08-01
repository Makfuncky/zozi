"""Permissions write service — DB write operations for permission entities."""
from sqlalchemy.orm import Session

from models import RolePermissionSetting


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