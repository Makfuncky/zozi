"""Find consumers of the legacy-only admin symbols outside controllers/admin/."""
import glob
import re

SYMBOLS = [
    "list_staff_accounts", "get_all_users", "update_user_role", "toggle_user_active",
    "bulk_update_users_role", "bulk_toggle_users_active", "create_staff_account",
    "update_staff_account", "delete_staff_account", "bulk_update_staff_accounts",
    "list_pending_bank_accounts", "verify_bank_account", "delete_bank_account_record",
    "refresh_admin_analytics_snapshots", "VALID_USER_ROLES",
]

for sym in SYMBOLS:
    consumers = []
    for path in glob.glob("backend/**/*.py", recursive=True):
        if "__pycache__" in path or "venv" in path or "backend/controllers/admin/" in path:
            continue
        src = open(path, encoding="utf-8", errors="ignore").read()
        if re.search(r"\b" + sym + r"\b", src):
            consumers.append(path)
    print(f"{sym:<32} -> {len(consumers)} consumers")
    for c in consumers:
        print(f"    {c}")
