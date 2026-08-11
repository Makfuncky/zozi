import ast, pathlib
ROOT = pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
SKIP = {"venv","__pycache__",".venv","node_modules",".pytest_cache"}
for p in ROOT.rglob("*.py"):
    if any(x in p.parts for x in SKIP): continue
    try: tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError: continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call): continue
        fn = node.func
        name = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else None)
        if name not in {"audit_log","_audit_log"}: continue
        kw = sorted(k.arg for k in node.keywords if k.arg)
        if set(kw) <= {"details","user_id"}:
            print(f"{p.relative_to(ROOT)}:{node.lineno} pos={len(node.args)} kw={kw}")
