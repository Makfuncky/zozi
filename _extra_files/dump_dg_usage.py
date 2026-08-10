"""For the remaining 37 DG violations, dump the offending import line(s)
and every usage of the imported names in that file, so we can decide
TYPE_CHECKING vs real refactor.
"""
from __future__ import annotations

import ast
from pathlib import Path

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")

# (file, target_module) from the scanner
VIOL = [
    ("backend/db/seed.py", "services.logistics_partner_pricing"),
    ("backend/dependencies/country_rls.py", "models"),
    ("backend/dependencies/fraud_events.py", "models.fraud"),
    ("backend/dependencies/coi_dependency.py", "services.coi_service"),
    ("backend/dependencies/country_detection.py", "services.country_detection"),
    ("backend/dependencies/country_rls.py", "services.logistics_partner_pricing"),
    ("backend/dependencies/fraud_events.py", "services"),
    ("backend/middleware/country_context.py", "models"),
    ("backend/middleware/country_context.py", "services.db_read"),
    ("backend/routers/supplier_orders.py", "providers.parcel_verification"),
    ("backend/routers/supplier_supplier_upload.py", "providers.bg_remover"),
    ("backend/routers/system_media_sync.py", "providers.async_workers"),
    ("backend/routers/system_media_sync.py", "providers.bg_remover"),
    ("backend/routers/system_media_sync.py", "providers.vision"),
    ("backend/routers/system_search_operations.py", "providers.image"),
    ("backend/routers/system_search_operations.py", "providers.voice_to_text"),
    ("backend/services/effective_permissions.py", "controllers.auth_controller"),
    ("backend/services/identity_admin_service.py", "controllers.customer.users"),
    ("backend/services/promotion_points_service.py", "controllers.promotion_controller"),
    ("backend/utils/csrf_utils.py", "middleware.csrf_middleware"),
    ("backend/utils/audit.py", "models"),
    ("backend/utils/category_tree.py", "models"),
    ("backend/utils/country_rls.py", "models"),
    ("backend/utils/dependencies.py", "models"),
    ("backend/utils/email_service.py", "models"),
    ("backend/utils/entity_messaging.py", "models"),
    ("backend/utils/key_rotation.py", "models"),
    ("backend/utils/order_tracking.py", "models"),
    ("backend/utils/realtime.py", "models"),
    ("backend/utils/rls_context.py", "models"),
    ("backend/utils/rls_interceptor.py", "models"),
    ("backend/utils/schema_audit.py", "models"),
    ("backend/utils/security_audit.py", "models"),
    ("backend/utils/vault.py", "models"),
    ("backend/utils/country_detection_middleware.py", "services.country_detection"),
    ("backend/utils/email_service.py", "services.email_event_service"),
    ("backend/utils/ml_worker.py", "services.bg_removal_service"),
]


def parse_safe(p):
    try:
        return ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def main():
    for rel, target in VIOL:
        f = BACKEND / rel
        print("=" * 90)
        print(f"{rel}   <-- {target}")
        tree = parse_safe(f)
        if tree is None:
            print("  (parse failed)")
            continue
        # find import statements matching target
        imported_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == target:
                line = node.lineno
                names = [a.name for a in node.names]
                imported_names.extend(names)
                snippet = f.read_text(encoding="utf-8", errors="ignore").splitlines()[line - 1]
                print(f"  IMPORT L{line}: {snippet.strip()}")
        # usage of each imported name
        txt = f.read_text(encoding="utf-8", errors="ignore")
        for name in sorted(set(imported_names)):
            lines = [i + 1 for i, l in enumerate(txt.splitlines()) if re_search(l, name)]
            print(f"  name '{name}' used on {len(lines)} line(s): {lines[:12]}{'...' if len(lines)>12 else ''}")


def re_search(line, name):
    import re
    return re.search(rf"(?<![\w.]){re.escape(name)}(?![\w])", line) is not None


if __name__ == "__main__":
    main()
