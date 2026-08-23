# AUTO-GENERATED controller delegator (routers -> controllers -> services).
"""services.users.identity_admin_service re-exports for HTTP routers."""
from domains.governance.services.user.identity_admin_service import archive_user
from domains.governance.services.user.identity_admin_service import bulk_archive_users
from domains.governance.services.user.identity_admin_service import bulk_restore_users
from domains.governance.services.user.identity_admin_service import bulk_toggle_active
from domains.governance.services.user.identity_admin_service import delete_user_admin
from domains.governance.services.user.identity_admin_service import force_reset_password
from domains.governance.services.user.identity_admin_service import get_user_by_id
from domains.governance.services.user.identity_admin_service import get_user_by_id_or_404
from domains.governance.services.user.identity_admin_service import hard_delete_user
from domains.governance.services.user.identity_admin_service import list_all_users
from domains.governance.services.user.identity_admin_service import list_users_by_country
from domains.governance.services.user.identity_admin_service import restore_user
from domains.governance.services.user.identity_admin_service import set_user_active
from domains.governance.services.user.identity_admin_service import set_user_role
from domains.governance.services.user.identity_admin_service import update_user_by_id
from domains.governance.services.user.identity_admin_service import update_user_in_country
