"""Auto-migrated service logic from routers/admin_users.py."""
from __future__ import annotations

from fastapi import Body, Depends, HTTPException, Path, Query

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest, UserAdminUpdate, UserOut

from domains.governance.models.user import User

from domains.country.utils.country_rls import get_country_or_404

from infrastructure.utils.dependencies import require_admin

from infrastructure.utils.pagination import paginated_response

from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context













from domains.governance.services.users.admin_identity_operations_api_service import list_users













from domains.governance.services.users.admin_identity_operations_service import update_user










from domains.governance.services.users.admin_identity_operations_service import archive_user












from domains.governance.services.users.admin_identity_operations_service import restore_user














from domains.governance.services.users.admin_identity_operations_service import toggle_user_active_route
from domains.governance.services.users.admin_identity_operations_service import reset_user_password


# === auto-wiring re-exports (migration repair) ===
from domains.governance.services.users.admin_identity_operations_service import bulk_archive_users
from domains.governance.services.users.admin_identity_operations_service import bulk_delete_users
from domains.governance.services.users.admin_identity_operations_service import bulk_restore_users
from domains.governance.services.users.admin_identity_operations_service import bulk_toggle_user_active
from domains.governance.services.users.admin_identity_operations_service import bulk_update_user_role
from domains.governance.services.users.admin_identity_operations_service import delete_user_permanent


