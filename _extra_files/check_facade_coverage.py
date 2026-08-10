"""Check whether the domain folder copies define the 19 live facade symbols."""
import re

SYMBOLS = [
    "require_admin", "require_roles", "require_country_access", "require_permission",
    "get_current_admin", "ROLE_PERMISSION_MAP", "load_role_permission_settings",
    "archive_entity", "restore_entity", "bulk_archive_entities", "bulk_restore_entities",
    "hard_delete_entity", "bulk_product_moderation", "bulk_category_change",
    "update_user_role", "toggle_user_active", "force_reset_password_admin",
    "delete_user_admin", "update_order_status", "refresh_admin_analytics_snapshots",
]

ADMIN_FILES = {
    "auth": "backend/controllers/admin/auth.py",
    "permissions": "backend/controllers/admin/permissions.py",
    "misc": "backend/controllers/admin/misc.py",
    "users": "backend/controllers/admin/users.py",
    "orders": "backend/controllers/admin/orders.py",
    "analytics": "backend/controllers/admin/analytics.py",
    "bulk_ops": "backend/controllers/admin/bulk_ops.py",
}
DOMAIN_FILES = {
    "auth": "backend/controllers/security/admin_auth.py",
    "permissions": "backend/controllers/permissions/permissions.py",
    "misc": "backend/controllers/audit/misc.py",
    "users": "backend/controllers/security/admin_users.py",
    "orders": "backend/controllers/orders/orders.py",
    "analytics": "backend/controllers/analytics/analytics.py",
    "bulk_ops": "backend/controllers/catalog/bulk_ops.py",
}


def defs_in(path):
    try:
        src = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return set()
    return set(re.findall(r"^(?:async )?def (\w+)", src, re.M)) | set(
        re.findall(r"^(\w+)\s*=", src, re.M)
    )


print(f"{'symbol':<32} {'admin':<8} {'domain':<8} covered")
for sym in SYMBOLS:
    admin_hit = None
    domain_hit = None
    for key, path in ADMIN_FILES.items():
        if sym in defs_in(path):
            admin_hit = key
    for key, path in DOMAIN_FILES.items():
        if sym in defs_in(path):
            domain_hit = key
    status = "OK" if domain_hit else ("MISSING" if admin_hit else "-")
    print(f"{sym:<32} {str(admin_hit):<8} {str(domain_hit):<8} {status}")
