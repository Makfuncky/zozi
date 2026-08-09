import os, sys, traceback
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
REPO = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
SYS = os.path.join(REPO, "scripts", "system_trackers", "system_architecture_audit.py")
sys.path.insert(0, os.path.join(REPO, "scripts", "system_trackers"))
import importlib.util
spec = importlib.util.spec_from_file_location("sa_audit", SYS)
m = importlib.util.module_from_spec(spec)
sys.modules["sa_audit"] = m
spec.loader.exec_module(m)

repo = m.find_repo(None)
eff = m.load_rules(repo, None)
m.ensure_required_ignore_dirs(eff)
m._ACTIVE_EFF = eff
rep = m.Report()
try:
    d = m.hl_run_all_checks(repo, rep, None)
    print("HEALTH OK ->", {k: (len(v) if isinstance(v, list) else v) for k, v in d.items()})
except Exception:
    print("HEALTH EXC:")
    traceback.print_exc()
print("HL findings so far:", sum(1 for f in rep.findings if f.code.startswith("HL")))
