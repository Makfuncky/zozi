"""Compute the public-symbol delta: legacy admin/* symbols missing from the domain union."""
import ast
import glob

ADMIN_FILES = sorted(glob.glob("backend/controllers/admin/*.py"))
ADMIN_FILES = [f for f in ADMIN_FILES if not f.endswith("__init__.py")]

DOMAIN_FILES = [
    "backend/controllers/security/admin_auth.py",
    "backend/controllers/security/admin_users.py",
    "backend/controllers/permissions/permissions.py",
    "backend/controllers/audit/misc.py",
    "backend/controllers/orders/orders.py",
    "backend/controllers/analytics/analytics.py",
    "backend/controllers/catalog/bulk_ops.py",
    "backend/controllers/catalog/products.py",
    "backend/controllers/supplier/suppliers.py",
    "backend/controllers/treasury/payouts.py",
    "backend/controllers/commerce/coupons.py",
    "backend/controllers/comms/tickets.py",
    "backend/controllers/configuration/database.py",
    "backend/controllers/identity/users.py",
]


def public_symbols(path):
    try:
        tree = ast.parse(open(path, encoding="utf-8", errors="ignore").read())
    except (OSError, SyntaxError):
        return set()
    syms = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                syms.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and not t.id.startswith("_"):
                    syms.add(t.id)
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                syms.add(node.name)
    return syms


admin_all = set()
for f in ADMIN_FILES:
    admin_all |= public_symbols(f)

domain_all = set()
for f in DOMAIN_FILES:
    domain_all |= public_symbols(f)

missing = sorted(admin_all - domain_all)
print(f"admin legacy public symbols: {len(admin_all)}")
print(f"domain union public symbols: {len(domain_all)}")
print(f"symbols ONLY in legacy admin (need porting): {len(missing)}")
for s in missing:
    # find which admin file defines it
    for f in ADMIN_FILES:
        if s in public_symbols(f):
            print(f"  {s:<45} <- {f.split('/')[-1]}")
            break
