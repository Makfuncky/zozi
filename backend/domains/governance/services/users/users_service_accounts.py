"""Auto-migrated service logic from routers/users.py."""
from __future__ import annotations

from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import UserAdminUpdate, UserOut, UserUpdate

from domains.governance.models.user import User

from infrastructure.utils.dependencies import get_current_user, require_admin


def _get_ports():
    """Lazy import to avoid circular dependency at module load."""
    from domains.governance.ports import (
        list_users, update_profile, get_user, admin_update_user,
    )
    return list_users, update_profile, get_user, admin_update_user
