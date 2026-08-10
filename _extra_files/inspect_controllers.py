import os, importlib.util, sys, traceback

backend = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
sys.path.insert(0, backend)
os.chdir(backend)

controllers_dir = os.path.join(backend, "controllers")
results = {}
for fn in sorted(os.listdir(controllers_dir)):
    if not fn.endswith(".py") or fn == "__init__.py":
        continue
    name = fn[:-3]
    mod = f"controllers.{name}"
    try:
        spec = importlib.util.spec_from_file_location(mod, os.path.join(controllers_dir, fn))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
    except Exception as e:
        results[name] = ("IMPORT_ERROR", str(e)[:120])
        continue
    has_router = hasattr(m, "router")
    routes = []
    if has_router:
        r = getattr(m, "router")
        try:
            for route in r.routes:
                methods = ",".join(sorted(getattr(route, "methods", []) or []))
                routes.append(f"{methods} {route.path}")
        except Exception:
            pass
    results[name] = ("router" if has_router else "no_router", routes)

for name, (kind, routes) in results.items():
    print(f"\n## {name}  [{kind}]")
    for r in routes:
        print("   ", r)
