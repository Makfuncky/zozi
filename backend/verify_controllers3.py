import ast, os, sys, importlib.util, importlib, tempfile, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from routers.generated import auto_router as ar

CONTROLLERS = os.path.join(ROOT, "controllers")

fastapi_real = set(); decorated = set()
for dp, _, files in os.walk(CONTROLLERS):
    for fn in files:
        if not fn.endswith(".py") or fn == "__init__.py": continue
        full = os.path.join(dp, fn)
        rel = os.path.relpath(full, ROOT).replace(os.sep, ".")
        mod = rel[:-3]
        tree = ast.parse(open(full, encoding="utf-8").read(), filename=full)
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
violations = sorted(fastapi_real & decorated)
print("Decorated modules:", len(modset), "| FastAPI-importing decorated (violation):", len(violations))
for v in violations: print("   VIOLATION:", v)

# Execute each generated router by writing to a temp file and importing it.
outdir = tempfile.mkdtemp(prefix="gen_routers_")
gen_fail=[]
for mi in modules:
    try: gen = ar.generate_router_file(mi)
    except Exception as e: gen_fail.append((mi["module"],"GENERATE:"+repr(e))); continue
    if not gen: continue
    safe = mi["module"].replace(".","_") + "_router.py"
    path = os.path.join(outdir, safe)
    open(path,"w",encoding="utf-8").write(gen)
    try:
        spec = importlib.util.spec_from_file_location("genmod_"+mi["module"].replace(".","_"), path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        if not hasattr(m, "router"):
            gen_fail.append((mi["module"], "no 'router' attribute"))
    except Exception as e:
        gen_fail.append((mi["module"], repr(e)))
        print("ROUTER-IMPORT-FAIL", mi["module"], "->", repr(e)[:260])
shutil.rmtree(outdir, ignore_errors=True)
print("\nGenerated routers that fail to import/execute:", len(gen_fail))
for g in gen_fail: print("   ", g)
print("\nSUMMARY: violations=", len(violations), "gen_fail=", len(gen_fail))
