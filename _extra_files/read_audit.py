import re
p = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\audit_run_red0.txt"
try:
    lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
except FileNotFoundError:
    print("output file not found yet")
    raise SystemExit
for ln in lines[:30]:
    print(ln)
print("---- RED lines in hotlist ----")
for ln in lines:
    if ln.startswith("🔴") or "VIOLATIONS" in ln:
        print(ln)
