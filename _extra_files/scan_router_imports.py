import os, re, ast, sys

ROUTERS = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\routers"
MARKER = "AUTO-GENERATED"

def is_handwritten(fp):
    try:
        t = open(fp, encoding="utf-8").read()
    except Exception:
        return False
    return MARKER not in t

def analyze(fp):
    text = open(fp, encoding="utf-8").read()
    tree = ast.parse(text)
    routes = []
    imports_controller = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                d = ast.unparse(dec)
                m = re.match(r"\w+\.(get|post|put|patch|delete)\(", d)
                if m:
                    routes.append((m.group(1).upper(), node.name))
    # detect inline logic smells
    db_refs = len(re.findall(r"\b(db|session|conn)\s*\.\s*(query|execute|add|commit|refresh|merge|delete)\b", text))
    service_inst = len(re.findall(r"=\s*\w*[Ss]ervice\s*\(|get_\w+_service\s*\(", text))
    get_db = "get_db" in text
    ctrl_imports = re.findall(r"from controllers\.[\w.]+ import (.+)", text)
    return {
        "routes": routes,
        "db_refs": db_refs,
        "service_inst": service_inst,
        "get_db": get_db,
        "ctrl_imports": ctrl_imports,
        "lines": text.count("\n")+1,
    }

files = []
for fn in sorted(os.listdir(ROUTERS)):
    if not fn.endswith(".py") or fn == "__init__.py":
        continue
    fp = os.path.join(ROUTERS, fn)
    if is_handwritten(fp):
        files.append((fn, fp))

print(f"HAND-WRITTEN ROUTERS: {len(files)}")
print()
# focus on ones importing decorated controllers
for fn, fp in files:
    a = analyze(fp)
    if a["ctrl_imports"]:
        print(f"### {fn}  (lines={a['lines']}, routes={len(a['routes'])}, db_refs={a['db_refs']}, svc_inst={a['service_inst']})")
        print(f"    imports controllers: {a['ctrl_imports']}")
        for r in a["routes"][:12]:
            print(f"      {r[0]:6} {r[1]}")
