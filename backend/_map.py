from __future__ import annotations
import ast, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTROLLERS = os.path.join(ROOT, "controllers")
ROUTERS = os.path.join(ROOT, "routers")

def calls_in(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Return, ast.Expr)):
            val = node.value
            if isinstance(val, ast.Await):
                val = val.value
            if isinstance(val, ast.Call) and isinstance(val.func, ast.Name):
                names.add(val.func.id)
    return names

def controller_funcs(fp):
    try:
        tree = ast.parse(open(fp, encoding="utf-8").read())
    except SyntaxError:
        return set()
    return {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

# build map: router file -> set of called func names
router_calls = {}
for fn in os.listdir(ROUTERS):
    if not fn.endswith(".py") or fn == "__init__.py":
        continue
    fp = os.path.join(ROUTERS, fn)
    text = open(fp, encoding="utf-8").read()
    if "AUTO-GENERATED" in text:
        continue
    try:
        tree = ast.parse(text)
    except SyntaxError:
        continue
    router_calls[fn] = calls_in(tree)

# for each plain controller, count referencing routers
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
        cfuncs = controller_funcs(fp)
        refs = [r for r, c in router_calls.items() if c & cfuncs]
        if refs:
            print(f"{rel}  [{len(refs)} routers]: {', '.join(refs)}")
