"""Pin the exact domain source for each live facade symbol."""
import re

SYMBOLS = [
    "require_admin", "require_roles", "require_country_access", "require_permission",
    "get_current_admin", "ROLE_PERMISSION_MAP", "load_role_permission_settings",
    "archive_entity", "restore_entity", "bulk_archive_entities", "bulk_restore_entities",
    "hard_delete_entity", "bulk_product_moderation", "bulk_category_change",
    "update_user_role", "toggle_user_active", "force_reset_password_admin",
    "delete_user_admin", "update_order_status", "refresh_admin_analytics_snapshots",
]

CANDIDATES = [
    "backend/controllers/security/admin_auth.py",
    "backend/controllers/security/admin_users.py",
    "backend/controllers/customer/users.py",
    "backend/controllers/permissions/permissions.py",
    "backend/controllers/audit/misc.py",
    "backend/controllers/catalog/bulk_ops.py",
    "backend/controllers/orders/orders.py",
    "backend/controllers/analytics/analytics.py",
]


def find_sym(path, sym):
    try:
        src = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return None
    # function def or module-level assignment or class
    for m in re.finditer(
        r"^(?:async\s+)?def\s+" + sym + r"\b|^" + sym + r"\s*=", src, re.M
    ):
        return src.count("\n", 0, m.start()) + 1
    return None


for sym in SYMBOLS:
    hits = [(p.split("/")[-1], find_sym(p, sym)) for p in CANDIDATES if find_sym(p, sym)]
    print(f"{sym:<34} {hits}")
