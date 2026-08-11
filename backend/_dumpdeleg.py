import ast, os, re

ROUTERS = os.path.join(os.getcwd(), "routers")


def prefix(text):
    m = re.search(r'APIRouter\(\s*prefix\s*=\s*"([^"]*)"', text)
    return m.group(1) if m else ""


for fn in sorted(os.listdir(ROUTERS)):
    if not fn.endswith(".py") or fn == "__init__.py":
        continue
    fp = os.path.join(ROUTERS, fn)
    try:
        text = open(fp, encoding="utf-8").read()
        tree = ast.parse(text)
    except Exception:
        continue
    pre = prefix(text)
    imports = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("controllers"):
            for a in n.names:
                imports[a.asname or a.name] = n.module
    for n in tree.body:
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        deco = None
        for d in n.decorator_list:
            if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr in ("get", "post", "put", "patch", "delete"):
                deco = d
                break
        if deco is None:
            continue
        tgt = None
        for sub in ast.walk(n):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id in imports:
                tgt = sub.func.id
                break
        if tgt:
            print(fn, "->", imports[tgt], "::", tgt)
