import importlib, glob, os, traceback
from collections import Counter
ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
import sys
sys.path.insert(0, os.path.join(ROOT, "backend"))
# load backend/.env if present
envp = os.path.join(ROOT, "backend", ".env")
if os.path.exists(envp):
    for line in open(envp, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-import-check-1234567890")

fails = []
ok = 0
for f in sorted(glob.glob(os.path.join(ROOT, "backend", "routers", "*.py"))):
    name = os.path.basename(f)[:-3]
    if name == "__init__":
        continue
    try:
        importlib.import_module(f"routers.{name}")
        ok += 1
    except Exception as e:
        fails.append((name, type(e).__name__, str(e).splitlines()[0]))

print(f"OK={ok} FAIL={len(fails)}")
c = Counter(t for _, t, _ in fails)
print("By error type:", dict(c))
print()
for name, t, msg in fails:
    print(f"{name} :: {t} :: {msg}")
