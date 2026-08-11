from __future__ import annotations
import ast, os, re
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTROLLERS = os.path.join(ROOT, "controllers")
ROUTERS = os.path.join(ROOT, "routers")

def router_imports(fp):
    """Return {controller_module: set(funcnames)} imported by a router."""
    out = defaultdict(set)
    try:
        tree = ast.parse(open(fp, encoding="utf-8").read())
    except SyntaxError:
        return out
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("controllers"):
            for a in n.names:
                out[n.module].add(a.asname or a.name)
    return out

# map controller module -> list of routers importing from it
mod_to_routers = defaultdict(list)
for fn in os.listdir(ROUTERS):
    if not fn.endswith(".py") or fn == "__init__.py":
        continue
    fp = os.path.join(ROUTERS, fn)
    text = open(fp, encoding="utf-8").read()
    if "AUTO-GENERATED" in text:
        continue
    imps = router_imports(fp)
    for mod in imps:
        mod_to_routers[mod].append((fn, imps[mod]))

for dirpath, _, files in os.walk(CONTROLLERS):
    for fn in files:
        if not fn.endswith(".py") or fn == "__init__.py":
            continue
        fp = os.path.join(dirpath, fn)
        text = open(fp, encoding="utf-8").read()
        if "from routers.generated.auto_router import" in text:
            continue
        if re.search(r"router\s*=\s*APIRouter", text):
            continue
        rel = os.path.relpath(fp, ROOT)[:-3].replace(os.sep, ".")
        refs = mod_to_routers.get(rel, [])
        tag = "ELIGIBLE-CANDIDATE" if len(refs) == 1 else ("SHARED(%d)" % len(refs))
        extra = ""
        if len(refs) == 1:
            extra = " funcs=%s" % sorted(refs[0][1])
        print(f"{rel:55} {tag} {extra}")
