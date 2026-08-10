import os, re, importlib, json, shutil, glob
from collections import defaultdict

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
BACKEND = os.path.join(ROOT, "backend")
ROUTERS = os.path.join(BACKEND, "routers")
TRASH = os.path.join(ROOT, "_extra_files", "_router_trash")
MAIN = os.path.join(BACKEND, "main.py")

moved = [l.strip() for l in open(os.path.join(ROOT, "_extra_files", "router_deleted_final.txt"), encoding="utf-8") if l.strip()]

# 1) remove stale .pyc for moved modules
removed_pyc = 0
for name in moved:
    base = name[:-3]
    for pc in glob.glob(os.path.join(ROUTERS, "__pycache__", base + "*.pyc")):
        os.remove(pc); removed_pyc += 1

# 2) parse live router_names from main.py
main_src = open(MAIN, encoding="utf-8", errors="replace").read()
m = re.search(r"router_names\s*=\s*\[(.*?)\]", main_src, re.S)
live_names = re.findall(r'\(\s*"([^"]+)"\s*,', m.group(1))

# 3) try importing every live router; ensure none is now missing/broken
import sys
sys.path.insert(0, BACKEND)
ok, fail = [], []
for nm in live_names:
    try:
        mod = importlib.import_module(f"routers.{nm}")
        if hasattr(mod, "router"):
            ok.append(nm)
        else:
            fail.append((nm, "no 'router' attr"))
    except Exception as e:
        fail.append((nm, repr(e)[:120]))

# 4) ensure NO moved file is in live_names and NO live router imports a moved module
moved_set = set(moved)
live_in_moved = [n for n in live_names if (n + ".py") in moved_set]

print("moved .py files        :", len(moved))
print("stale .pyc removed     :", removed_pyc)
print("live router names       :", len(live_names))
print("live imported OK        :", len(ok))
print("live FAILED             :", len(fail))
for n, e in fail:
    print("   FAIL", n, "-", e)
print("live names that were moved (MUST BE 0):", live_in_moved)
print()
# 5) remaining .py count in routers
remaining = [f for f in os.listdir(ROUTERS) if f.endswith(".py")]
print("remaining router .py files:", len(remaining))
