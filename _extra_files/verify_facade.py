"""Verify the rewritten facade exposes every legacy admin symbol."""
import ast
import sys

sys.path.insert(0, "backend")

ADMIN_FILES = [
    "backend/controllers/admin/analytics.py",
    "backend/controllers/admin/auth.py",
    "backend/controllers/admin/bulk_ops.py",
    "backend/controllers/admin/coupons.py",
    "backend/controllers/admin/database.py",
    "backend/controllers/admin/misc.py",
    "backend/controllers/admin/orders.py",
    "backend/controllers/admin/payouts.py",
    "backend/controllers/admin/permissions.py",
    "backend/controllers/admin/products.py",
    "backend/controllers/admin/suppliers.py",
    "backend/controllers/admin/tickets.py",
    "backend/controllers/admin/users.py",
]


def public_symbols(path):
    tree = ast.parse(open(path, encoding="utf-8", errors="ignore").read())
    syms = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            syms.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and not t.id.startswith("_"):
                    syms.add(t.id)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            syms.add(node.name)
    return syms


legacy = set()
for f in ADMIN_FILES:
    legacy |= public_symbols(f)

import controllers.admin_controller as facade  # noqa: E402

missing = sorted(s for s in legacy if not hasattr(facade, s))
print(f"legacy symbols: {len(legacy)}")
print(f"facade has {len(legacy) - len(missing)}/{len(legacy)}")
if missing:
    print("MISSING:", missing)
else:
    print("ALL LEGACY SYMBOLS EXPOSED")
