import os, ast, sys
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
from rbac.catalog import FEATURE_CATALOG, all_features
from domains.governance.services.effective_permissions import HR_PERMISSION_MAP

def _is_rf(node):
    if not isinstance(node, ast.Call): return False
    f = node.func
    if isinstance(f, ast.Name): return f.id == "require_feature"
    if isinstance(f, ast.Attribute): return f.attr == "require_feature"
    return False

EXCLUDES = {"venv", ".git", "__pycache__", "_extra_files", "tests"}
root = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
used = set()
for dp, dn, fns in os.walk(root):
    dn[:] = [d for d in dn if d not in EXCLUDES]
    for fn in fns:
        if not fn.endswith(".py"): continue
        p = os.path.join(dp, fn)
        try:
            if "require_feature" not in open(p, encoding="utf-8").read():
                continue
            tree = ast.parse(open(p, encoding="utf-8").read())
        except Exception:
            continue
        for n in ast.walk(tree):
            if _is_rf(n) and n.args:
                a = n.args[0]
                if isinstance(a, ast.Constant) and isinstance(a.value, str) and "*" in a.value:
                    used.add(a.value)

def prefix(wc):
    return wc.split(".")[0]

used_prefixes = {prefix(w) for w in used}
all_atoms = set(all_features()) | set(HR_PERMISSION_MAP.keys())
backed_prefixes = {prefix(a) for a in all_atoms if "." in a}

print("wildcard literals used in code:", sorted(used))
print("prefixes used:                ", sorted(used_prefixes))
print("prefixes w/ backing atoms:    ", sorted(backed_prefixes))
print()
print("used - backed (would fail test1, atomless wildcards):", sorted(used_prefixes - backed_prefixes))
print("backed - used (would fail test2, dead declarations):", sorted(backed_prefixes - used_prefixes))
print()
print("FEATURE_NAMESPACES = used  &  backed :", sorted(used_prefixes & backed_prefixes))
