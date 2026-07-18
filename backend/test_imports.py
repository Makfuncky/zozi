import sys, os, importlib, traceback

backend_dir = r"F:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
sys.path.insert(0, backend_dir)

errors = []
success = []
router_dir = os.path.join(backend_dir, "routers")
routers = [f.replace(".py","") for f in os.listdir(router_dir) if f.endswith(".py") and f != "__init__.py"]

for r in sorted(routers):
    try:
        importlib.import_module(f"routers.{r}")
        success.append(r)
    except Exception as e:
        tb = traceback.format_exc()
        errors.append(f"{r}: {e}\n{tb}")

print("=== SUCCESSFUL IMPORTS ===")
for s in success:
    print(f"  OK: {s}")
print(f"\nTotal successful: {len(success)}")
print(f"\n=== IMPORT ERRORS ===")
for e in errors:
    print(e)
print(f"Total errors: {len(errors)}")

