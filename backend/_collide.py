import ast, os, re

ROUTERS = os.path.join(os.getcwd(), "routers")
seen = {}
dups = []


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
    for n in tree.body:
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for d in n.decorator_list:
            if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr in ("get", "post", "put", "patch", "delete"):
                path = d.args[0].value if d.args and isinstance(d.args[0], ast.Constant) else None
                if path is None:
                    continue
                full = (pre + path) if path.startswith("/") else (pre + "/" + path)
                key = (d.func.attr.upper(), full)
                if key in seen:
                    dups.append((key, seen[key], fn))
                else:
                    seen[key] = fn

if dups:
    print("DUPLICATE (METHOD, path) registrations that would crash startup:")
    for key, a, b in dups:
        print(f"  {key[0]:7} {key[1]:50} in {a} AND {b}")
else:
    print("OK — no (METHOD, path) collisions across all routers")
