import json
import re
from pathlib import Path

REPO = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
PLAN = REPO / "scripts" / "system_trackers" / "_services_plan.json"
REG = REPO / "backend/services/_registry.py"

plan = json.loads(PLAN.read_text(encoding="utf-8"))
s2f = {}
for e in plan:
    if e["folder"] == "SCRATCH":
        continue
    s2f[e["file"][:-3]] = e["final_folder"]

raw = REG.read_bytes()
try:
    text = raw.decode("utf-8-sig")
except UnicodeDecodeError:
    text = raw.decode("utf-16")
out = []
changed = 0
for line in text.splitlines(keepends=True):
    new = line
    m = re.match(r"^(\s*import\s+)services\.(\w+)\s*$", line)
    if m and m.group(2) in s2f:
        new = f"{m.group(1)}services.{s2f[m.group(2)]}.{m.group(2)}\n"
        changed += 1
    m2 = re.match(r"^(\s*from\s+)services\.(\w+)(\s+import\s+)", line)
    if m2 and m2.group(2) in s2f:
        new = f"{m2.group(1)}services.{s2f[m2.group(2)]}.{m2.group(2)}{m2.group(3)}"
        changed += 1
    out.append(new)
REG.write_text("".join(out), encoding="utf-8")  # normalize to UTF-8
print("registry lines changed:", changed)
# show changed lines
for line in out:
    if line.strip().startswith("import services.") and ".services." not in line and line.count(".") == 2:
        pass
print("remaining flat-style imports (should be 0):")
for line in out:
    s = line.strip()
    if s.startswith("import services.") or s.startswith("from services."):
        if re.match(r"^(import|from)\s+services\.\w+\s*$", s) or re.match(r"^from\s+services\.\w+\s+import", s):
            print("  FLAT:", s)
