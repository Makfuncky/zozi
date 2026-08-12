import ast, os, sys, py_compile, tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from routers.generated import auto_router as ar

CONTROLLERS = os.path.join(ROOT, "controllers")

fastapi_real = []
decorated_mods = []
for dp, _, files in os.walk(CONTROLLERS):
    for fn in files:
        if not fn.endswith(".py") or fn == "__init__.py":
            continue
        full = os.path.join(dp, fn)
        rel = os.path.relpath(full, ROOT).replace(os.sep, ".")
        mod = rel[:-3]
        try:
            tree = ast.parse(open(full, encoding="utf-8").read(), filename=full)
        except SyntaxError as e:
            print("SYNTAXERR", mod, e); continue
        has_route = False; has_fastapi = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id in ("route","get","post","put","patch","delete"):
                        has_route = True
            if isinstance(node, ast.ImportFrom) and node.module == "fastapi":
                has_fastapi = True
            if isinstance(node, ast.Import):
                for n in node.names:
                    if n.name == "fastapi": has_fastapi = True
        if has_fastapi: fastapi_real.append(mod)
        if has_route: decorated_mods.append(mod); print("DECORATED", mod)

print("\nTotal controllers:", len([1 for dp,_,files in os.walk(CONTROLLERS) for fn in files if fn.endswith('.py') and fn!='__init__.py']))
print("Controllers importing fastapi:", len(fastapi_real))
for m in fastapi_real: print("   FASTAPI-IMPORT:", m)

modules = ar.scan_controllers()
print("\nGenerator-discovered decorated modules:", len(modules))
print("Sum of routes:", sum(len(m['routes']) for m in modules))
errors = []
for mi in modules:
    try:
        gen = ar.generate_router_file(mi)
    except Exception as e:
        print("GENERATE-FAIL", mi["module"], repr(e)); errors.append(("GENERATE-FAIL", mi["module"], repr(e))); continue
    if not gen:
        print("COLLIDES-ALL (no router emitted):", mi["module"]); continue
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
            tf.write(gen); tmp = tf.name
        py_compile.compile(tmp, doraise=True)
    except py_compile.PyCompileError as e:
        print("COMPILE-FAIL", mi["module"]); errors.append(("COMPILE-FAIL", mi["module"], str(e)))
    finally:
        try: os.remove(tmp)
        except: pass

print("\nGenerator errors:", len(errors))
for e in errors: print("  ", e)

# Decorated-but-not-in-generator-scan? (should be empty; scan walks all)
missing = [m for m in decorated_mods if m not in {x['module'] for x in modules}]
print("\nDecorated controllers NOT discovered by generator:", missing)
