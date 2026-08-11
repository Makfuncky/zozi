import re
import subprocess
import sys
from pathlib import Path

REPO = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
BACKEND = REPO / "backend"
SERVICES = BACKEND / "services"

domains = {p.name for p in SERVICES.iterdir()
           if p.is_dir() and p.name not in ("__pycache__",)}
print("domain folders:", sorted(domains))

# 1) py_compile the services tree
r = subprocess.run([sys.executable, "-m", "py_compile"] + [str(p) for p in SERVICES.rglob("*.py")],
                   capture_output=True, text=True)
print("py_compile services:", "OK" if r.returncode == 0 else "FAIL")
if r.returncode != 0:
    print(r.stderr[:2000])

# 2) detect leftover flat references: services.<first> where first not a domain folder
ref_re = re.compile(r"services\.([A-Za-z_]\w*)")
leftover = {}
for p in BACKEND.rglob("*.py"):
    if "__pycache__" in p.parts:
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    for m in ref_re.finditer(t):
        first = m.group(1)
        if first not in domains:
            leftover.setdefault(first, str(p.relative_to(REPO)))
print("LEFT-OVER FLAT references (services.<non-domain>):", len(leftover))
for k, v in sorted(leftover.items()):
    print(f"  services.{k}  in {v}")
