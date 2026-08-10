"""Map every admin legacy public symbol to a canonical domain source file."""
import ast

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

DOMAIN_FILES = [
    "backend/controllers/security/admin_auth.py",
    "backend/controllers/security/admin_users.py",
    "backend/controllers/customer/users.py",
    "backend/controllers/permissions/permissions.py",
    "backend/controllers/audit/misc.py",
    "backend/controllers/catalog/bulk_ops.py",
    "backend/controllers/catalog/products.py",
    "backend/controllers/orders/orders.py",
    "backend/controllers/analytics/analytics.py",
    "backend/controllers/commerce/coupons.py",
    "backend/controllers/treasury/payouts.py",
    "backend/controllers/supplier/suppliers.py",
    "backend/controllers/comms/tickets.py",
    "backend/controllers/configuration/database.py",
    "backend/services/admin_analytics_service.py",
]


def public_symbols(path):
    try:
        tree = ast.parse(open(path, encoding="utf-8", errors="ignore").read())
    except (OSError, SyntaxError):
        return set()
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


domain_syms = {}
for f in DOMAIN_FILES:
    domain_syms[f] = public_symbols(f)

# reverse map: symbol -> [domain files defining it]
rev = {}
for f, syms in domain_syms.items():
    for s in syms:
        rev.setdefault(s, []).append(f)

unmapped = []
for f in ADMIN_FILES:
    for s in public_symbols(f):
        sources = rev.get(s, [])
        status = "OK" if sources else "UNMAPPED"
        if not sources:
            unmapped.append((s, f))
        print(f"{s:<38} {status:<9} {[x.split('/')[-1] for x in sources]}")

print(f"\nUNMAPPED ({len(unmapped)}): {[s for s, _ in unmapped]}")
