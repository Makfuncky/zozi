import os, sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
REPO = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
SYS = os.path.join(REPO, "scripts", "system_trackers", "system_architecture_audit.py")
sys.path.insert(0, os.path.join(REPO, "scripts", "system_trackers"))
import importlib.util
spec = importlib.util.spec_from_file_location("sa_audit", SYS)
m = importlib.util.module_from_spec(spec)
sys.modules["sa_audit"] = m
spec.loader.exec_module(m)

OUT = os.path.join(REPO, "_extra_files", "audit_findings_full.json")

def _capture(repo, rep, out, summary, placements, eff, reg, graph):
    rows = []
    for f in rep.findings:
        rows.append({
            "sev": getattr(f, "sev", ""),
            "code": getattr(f, "code", ""),
            "domain": getattr(f, "domain", ""),
            "path": getattr(f, "path", ""),
            "line": getattr(f, "line", None),
            "message": getattr(f, "message", ""),
            "priority": getattr(f, "priority", ""),
        })
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1)
    print("CAPTURED", len(rows), "findings ->", OUT)

m.render_markdown = _capture
rc = m.main()
print("MAIN_RC", rc)
