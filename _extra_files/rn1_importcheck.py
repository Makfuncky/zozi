import importlib, traceback, os
ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
import sys
sys.path.insert(0, os.path.join(ROOT, "backend"))
os.environ.setdefault("PYTHONPATH", os.path.join(ROOT, "backend"))
fails = []
ok = 0
import glob
for f in sorted(glob.glob(os.path.join(ROOT, "backend", "routers", "*.py"))):
    name = os.path.basename(f)[:-3]
    if name == "__init__":
        continue
    try:
        importlib.import_module(f"routers.{name}")
        ok += 1
    except Exception as e:
        fails.append((name, repr(e)))
print(f"OK={ok} FAIL={len(fails)}")
for name, e in fails:
    print("\n=== FAIL:", name, "===")
    print(e)
