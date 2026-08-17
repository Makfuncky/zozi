import ast, os, sys

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
EXCLUDE = {"venv", "__pycache__", ".git", "node_modules"}

# 1) Build filemap: dotted module name -> file path
filemap = {}
def walk():
    for dirpath, dirs, files in os.walk(ROOT):
        relparts = set(os.path.relpath(dirpath, ROOT).split(os.sep))
        if relparts & EXCLUDE:
            dirs[:] = []
            continue
        for f in files:
            if not f.endswith(".py"):
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, ROOT)[:-3].replace(os.sep, ".")
            if rel.endswith(".__init__"):
                rel = rel[:-9]
            filemap.setdefault(rel, full)

walk()

# 2) Build namespace map: module -> set of exported top-level names
namespace = {}
def collect(mod, path):
    try:
        src = open(path, encoding="utf-8", errors="ignore").read()
        tree = ast.parse(src, filename=path)
    except Exception:
        namespace[mod] = set()
        return
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.asname or a.name.split(".")[-1])
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                if a.name == "*":
                    continue
                names.add(a.asname or a.name)
    namespace[mod] = names

for mod, path in filemap.items():
    collect(mod, path)

def resolve_abs(base_parts):
    cand = ".".join(base_parts)
    if cand in filemap:
        return cand
    if (cand + ".__init__") in filemap:
        return cand + ".__init__"
    return None

# 3) Scan target packages for broken `from T import N`
PKGS = ["controllers", "services", "models", "routers"]
breaks = []

def check_module(mod, path):
    try:
        src = open(path, encoding="utf-8", errors="ignore").read()
        tree = ast.parse(src, filename=path)
    except Exception:
        return
    cur_is_pkg = mod.endswith(".__init__") or path.endswith("__init__.py")
    parts = mod.split(".")
    if cur_is_pkg:
        pkg_parts = parts[:]
    else:
        pkg_parts = parts[:-1]
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        level = node.level or 0
        modname = node.module
        if level:
            anchors = pkg_parts[:len(pkg_parts) - (level - 1)]
            if modname:
                base_parts = anchors + modname.split(".")
            else:
                base_parts = anchors
        else:
            if not modname:
                continue
            base_parts = modname.split(".")
        target = resolve_abs(base_parts)
        if target is None:
            # module itself does not exist
            for a in node.names:
                if a.name != "*":
                    breaks.append((mod, ".".join(base_parts), a.name, "MODULE_NOT_FOUND"))
            continue
        ns = namespace.get(target, set())
        for a in node.names:
            if a.name == "*":
                continue
            if a.name not in ns:
                breaks.append((mod, target, a.name, "NAME_MISSING"))

for mod, path in filemap.items():
    top = mod.split(".")[0]
    if top in PKGS:
        check_module(mod, path)

print("MODULES:", len(filemap), "BREAKS:", len(breaks))
print("=" * 90)
# Group by missing name
from collections import defaultdict
byname = defaultdict(list)
for mod, tgt, name, kind in breaks:
    byname[(name, kind)].append((mod, tgt))

for (name, kind), occ in sorted(byname.items(), key=lambda kv: (-len(kv[1]), kv[0][0])):
    print(f"### {name} ({kind}) — {len(occ)} refs")
    seen = set()
    for mod, tgt in occ:
        key = (mod, tgt)
        if key in seen:
            continue
        seen.add(key)
        print(f"   {mod}  ->  {tgt}")
