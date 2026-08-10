"""AST-verify the rewritten facade without importing models (agent churn).

1. Every `from X import Y` in the facade resolves to a public symbol in X's AST.
2. Every one of the 84 legacy admin symbols is re-exported by the facade.
"""
import ast
import sys

BACKEND = "backend"
sys.path.insert(0, BACKEND)

FACADE = "backend/controllers/admin_controller.py"
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
    try:
        tree = ast.parse(open(path, encoding="utf-8", errors="ignore").read())
    except (OSError, SyntaxError) as e:
        print(f"  !! cannot parse {path}: {e}")
        return set()
    syms = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            syms.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name) and not t.id.startswith("_"):
                    syms.add(t.id)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            syms.add(node.name)
    return syms


# 1. Resolve every facade import
tree = ast.parse(open(FACADE, encoding="utf-8", errors="ignore").read())
bad = []
imported_names = set()
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom) and node.module:
        mod = node.module.replace(".", "/") + ".py"
        path = f"{BACKEND}/{mod}"
        targets = public_symbols(path)
        for alias in node.names:
            imported_names.add(alias.name)
            if alias.name not in targets and alias.name != "*":
                bad.append((node.module, alias.name))
if bad:
    print("IMPORTS FAILING TO RESOLVE:")
    for m, n in bad:
        print(f"  {m} -> {n}")
else:
    print(f"ALL facade imports resolve ({len(imported_names)} names)")

# 2. 84-symbol coverage
legacy = set()
for f in ADMIN_FILES:
    legacy |= public_symbols(f)
missing = sorted(s for s in legacy if s not in imported_names and s != "logger")
print(f"legacy symbols: {len(legacy)}")
print(f"facade re-exports: {len(imported_names)}")
if missing:
    print("MISSING from facade:", missing)
else:
    print("ALL LEGACY SYMBOLS RE-EXPORTED (except incidental 'logger')")
