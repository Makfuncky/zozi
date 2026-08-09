import os, sys
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
rep = m.Report()
m.check_router_outside(repo, rep, eff)
m.check_layer_writes(repo, rep, eff)
m.check_controller_outside(repo, rep, eff)

bb = [f for f in rep.findings if "badge" in f.path.lower() or "badge" in (f.message or "").lower()]
print("=== badge_billing findings:", len(bb))
for f in bb:
    print(f.sev, f.code, f.path, "L"+str(f.line), f.message)
print("=== totals R1/W1 for all:", sum(1 for f in rep.findings if f.code in ("R1","W1")))
print("=== R1 count:", sum(1 for f in rep.findings if f.code=="R1"))
print("=== W1 count:", sum(1 for f in rep.findings if f.code=="W1"))
print("=== LIVE W1 findings (file:line) ===")
for f in sorted(rep.findings, key=lambda x: (x.path, x.line or 0)):
    if f.code == "W1":
        print(f.path, "L"+str(f.line), "|", f.message)
