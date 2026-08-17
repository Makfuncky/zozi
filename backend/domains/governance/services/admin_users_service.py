"""Auto-migrated service logic from routers/admin_users.py."""
from __future__ import annotations

from fastapi import Body, Depends, HTTPException, Path, Query

from sqlalchemy.orm import Session

from modules.admin.routers.admin_controller import (
    archive_entity,
    bulk_archive_entities,
    bulk_restore_entities,
    delete_user_admin,
    force_reset_password_admin,
    hard_delete_entity,
    restore_entity,
    toggle_user_active,
    update_user_role,
)

from infrastructure.database.database import get_db

from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest, UserAdminUpdate, UserOut

from models import User

from infrastructure.utils.country_rls import get_country_or_404

from infrastructure.utils.dependencies import require_admin

from infrastructure.utils.pagination import paginated_response

from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context













from services.admin.admin_identity_operations_api_service import list_users  # [MIGRATION COMPAT] re-export relocated symbol













from services.admin.admin_identity_operations_service import update_user  # [MIGRATION COMPAT] re-export relocated symbol










from services.admin.admin_identity_operations_service import archive_user  # [MIGRATION COMPAT] re-export relocated symbol












from services.admin.admin_identity_operations_service import restore_user  # [MIGRATION COMPAT] re-export relocated symbol














from services.admin.admin_identity_operations_service import toggle_user_active_route  # [MIGRATION COMPAT] re-export relocated symbol
from services.admin.admin_identity_operations_service import reset_user_password  # [MIGRATION COMPAT] re-export relocated symbol


# === auto-wiring re-exports (migration repair) ===
from services.admin.admin_identity_operations_service import (
    bulk_archive_users,
    bulk_delete_users,
    bulk_restore_users,
    bulk_toggle_user_active,
    bulk_update_user_role,
    delete_user_permanent
)


