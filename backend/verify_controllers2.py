import ast, os, sys, importlib.util, importlib

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from routers.generated import auto_router as ar

CONTROLLERS = os.path.join(ROOT, "controllers")

fastapi_real = set()
decorated = set()
for dp, _, files in os.walk(CONTROLLERS):
    for fn in files:
        if not fn.endswith(".py") or fn == "__init__.py": continue
        full = os.path.join(dp, fn)
        rel = os.path.relpath(full, ROOT).replace(os.sep, ".")
        mod = rel[:-3]
        try: tree = ast.parse(open(full, encoding="utf-8").read(), filename=full)
        except SyntaxError as e: print("SYNTAXERR", mod, e); continue
        has_route=False; has_fapi=False
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    if isinstance(dec,ast.Call) and isinstance(dec.func,ast.Name) and dec.func.id in ("route","get","post","put","patch","delete"):
                        has_route=True
            if isinstance(node,ast.ImportFrom) and node.module=="fastapi": has_fapi=True
            if isinstance(node,ast.Import):
                for n in node.names:
                    if n.name=="fastapi": has_fapi=True
        if has_fapi: fastapi_real.add(mod)
        if has_route: decorated.add(mod)

modules = ar.scan_controllers()
modset = {m["module"] for m in modules}
violations = sorted(fastapi_real & decorated)   # decorated AND imports fastapi
print("=== DECORATED modules:", len(modset))
print("=== FASTAPI-IMPORTING decorated controllers (contract violation):", len(violations))
for v in violations: print("   ", v)

# A) Import each DECORATED controller module directly (catch import-time errors)
print("\n--- Importing each decorated controller module ---")
import_fail = []
for m in sorted(modset):
    try:
        importlib.import_module(m)
    except Exception as e:
        import_fail.append((m, repr(e)))
        print("IMPORT-FAIL", m, "->", repr(e))
print("Decorated controllers that fail to import:", len(import_fail))

# B) Execute each GENERATED router (resolves `from {mod} import ...` + deps)
print("\n--- Executing each generated router module ---")
gen_fail = []
for mi in modules:
    try:
        gen = ar.generate_router_file(mi)
    except Exception as e:
        gen_fail.append((mi["module"], "GENERATE:"+repr(e))); continue
    if not gen:
        continue
    try:
        spec = importlib.util.spec_from_file_location("__gen_" + mi["module"].replace(".","_"),
                                                      "<string>")
        mod = importlib.util.module_from_spec(spec)
        mod.__dict__["__name__"] = "__gen_" + mi["module"].replace(".","_")
        exec(compile(gen, f"<gen {mi['module']}>", "exec"), mod.__dict__)
    except Exception as e:
        gen_fail.append((mi["module"], repr(e)))
        print("ROUTER-EXEC-FAIL", mi["module"], "->", repr(e)[:200])
print("Generated routers that fail to execute:", len(gen_fail))
for g in gen_fail: print("   ", g)

print("\nSUMMARY: violations=", len(violations), "import_fail=", len(import_fail), "gen_fail=", len(gen_fail))
