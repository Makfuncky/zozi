import os, sys, glob, importlib, traceback
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
os.environ["APP_ENV"] = "development"
os.environ["PROMETHEUS_MULTIPROC_DIR"] = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\prom_tmp"
B = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
# Prime deps first (db, utils) so routers can resolve
for core in ["utils.config", "db.database", "db.base", "utils.dependencies"]:
    try:
        __import__(core)
    except Exception:
        pass
ok = 0; fail = 0
errs = {}
files = sorted(glob.glob(os.path.join(B, "routers", "**", "*.py"), recursive=True))
for p in files:
    if os.path.basename(p) == "__init__.py":
        continue
    mod = "routers." + os.path.relpath(p, os.path.join(B, "routers"))[:-3].replace(os.sep, ".")
    # purge any previously imported copy so we truly re-import
    for k in [k for k in list(sys.modules) if k == mod or k.startswith(mod + ".")]:
        del sys.modules[k]
    try:
        importlib.import_module(mod)
        ok += 1
    except Exception as e:
        fail += 1
        msg = str(e).splitlines()[-1][:170]
        errs[msg] = errs.get(msg, 0) + 1
with open(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\rt_clean.txt", "w") as f:
    f.write(f"OK {ok} FAIL {fail}\n")
    for k, v in sorted(errs.items(), key=lambda x: -x[1]):
        f.write(f"  [{v}] {k}\n")
