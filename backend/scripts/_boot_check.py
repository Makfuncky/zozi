import os, sys, importlib, traceback

os.environ.setdefault("DATABASE_URL", "sqlite:///./_boot_test.db")
os.environ.setdefault("SECRET_KEY", "boot-test-secret-key-not-for-prod")
os.environ.setdefault("PYTHONPATH", os.path.dirname(os.path.abspath(__file__)))

try:
    import main
    print("MAIN IMPORT: OK")
except Exception as e:
    print("MAIN IMPORT: FAIL")
    traceback.print_exc()
    sys.exit(1)

app = getattr(main, "app", None)
if app is None:
    print("NO app object")
    sys.exit(1)

routes = [r for r in app.routes]
print("TOTAL ROUTES (incl. mounted):", len(routes))
paths = set()
for r in routes:
    p = getattr(r, "path", None)
    if p:
        paths.add(p)
print("UNIQUE PATH TEMPLATES:", len(paths))

# Per-module router import check
import importlib

modules_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")
for m in sorted(os.listdir(modules_dir)):
    rdir = os.path.join(modules_dir, m, "routers")
    if not os.path.isdir(rdir):
        continue
    ok = []
    bad = []
    for f in sorted(os.listdir(rdir)):
        if not f.endswith(".py") or f == "__init__.py":
            continue
        mod = f"modules.{m}.routers.{f[:-3]}"
        try:
            importlib.import_module(mod)
            ok.append(f)
        except Exception as e:
            bad.append((f, repr(e)[:200]))
    print(f"MODULE {m}: ok={len(ok)} bad={len(bad)}")
    for f, e in bad:
        print(f"   BAD {f}: {e}")
