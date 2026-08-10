"""Inventory all legacy admin public symbols grouped by their source file."""
import ast
import glob

ADMIN_FILES = sorted(
    f for f in glob.glob("backend/controllers/admin/*.py")
    if not f.endswith("__init__.py")
)


def public_symbols(path):
    tree = ast.parse(open(path, encoding="utf-8", errors="ignore").read())
    syms = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            syms[node.name] = "def"
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and not t.id.startswith("_"):
                    syms[t.id] = "var"
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            syms[node.name] = "class"
    return syms


total = 0
for f in ADMIN_FILES:
    syms = public_symbols(f)
    total += len(syms)
    print(f"{f.split('/')[-1]:<16} ({len(syms):2d}):")
    print("    " + ", ".join(sorted(syms)))
print(f"TOTAL: {total} symbols across {len(ADMIN_FILES)} files")
