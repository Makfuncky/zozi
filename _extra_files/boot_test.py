import sys, os, traceback
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")

# Try to import main and surface real errors (module-level exceptions, not silenced ImportErrors)
ok = True
try:
    import main
    print("IMPORT main: OK")
    # Now actually trigger router loading by inspecting registered routes
    routes = [getattr(r, "path", None) for r in main.app.routes]
    print("TOTAL ROUTES:", len(routes))
except Exception:
    ok = False
    traceback.print_exc()

if not ok:
    sys.exit(1)
