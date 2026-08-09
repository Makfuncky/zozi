"""One-off: delete the dead AnomalyDetector class (lines 24-128, 1-indexed)."""
from pathlib import Path

p = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\middleware\behavioral_analytics.py")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
# 1-indexed 24..128 inclusive -> python 0-indexed 23..127
kept = lines[:23] + lines[128:]
with open(p, "w", encoding="utf-8", newline="") as f:
    f.write("".join(kept))
print("removed lines 24-128; new line count:", len(kept))
print("line 23:", repr(lines[22]))
print("new line 24:", repr(kept[23]))
