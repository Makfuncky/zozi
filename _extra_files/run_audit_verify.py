import os, sys, traceback, datetime

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

REPO = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
SYS = os.path.join(REPO, "scripts", "system_trackers", "system_architecture_audit.py")
LOG = os.path.join(REPO, "_extra_files", "audit_verify.log")
sys.path.insert(0, os.path.join(REPO, "scripts", "system_trackers"))

import importlib.util
spec = importlib.util.spec_from_file_location("sa_audit", SYS)
m = importlib.util.module_from_spec(spec)
sys.modules["sa_audit"] = m
spec.loader.exec_module(m)

m.render_markdown = lambda *a, **k: None  # prevent clobbering canonical report

def log(*a):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(" ".join(str(x) for x in a) + "\n")
        f.flush()

log("START", datetime.datetime.now().isoformat())
rc = None
try:
    rc = m.main()
except SystemExit as e:
    rc = e.code
except Exception:
    rc = "EXC"
    with open(LOG, "a", encoding="utf-8") as f:
        traceback.print_exc(file=f)
log("END rc=", rc, datetime.datetime.now().isoformat())
