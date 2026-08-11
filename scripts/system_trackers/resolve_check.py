import re
from pathlib import Path

REPO = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
BACKEND = REPO / "backend"
SERVICES = BACKEND / "services"
domains = {p.name for p in SERVICES.iterdir() if p.is_dir() and p.name != "__pycache__"}

ref_re = re.compile(r"services\.([A-Za-z_]\w*)(?:\.([A-Za-z_]\w*))?")
missing = {}
files_checked = 0
for p in BACKEND.rglob("*.py"):
    if "__pycache__" in p.parts or "venv" in p.parts:
        continue
    files_checked += 1
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    for m in ref_re.finditer(t):
        d = m.group(1)
        mod = m.group(2)
        if d not in domains:
            continue  # not a services domain import (e.g. services.core in comment handled separately)
        if mod is None:
            # services.<domain> package import
            if not (SERVICES / d / "__init__.py").exists():
                missing.setdefault(f"services.{d}", str(p.relative_to(REPO)))
            continue
        cand = SERVICES / d / f"{mod}.py"
        pkg = SERVICES / d / mod / "__init__.py"
        if not cand.exists() and not pkg.exists():
            missing.setdefault(f"services.{d}.{mod}", str(p.relative_to(REPO)))

print(f"files checked: {files_checked}")
print("UNRESOLVED services.<domain>.<module> references:", len(missing))
for k, v in sorted(missing.items()):
    print(f"  {k}  <-  {v}")
