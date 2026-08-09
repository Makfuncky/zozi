import sys, re
tmp = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\tests\_extra_files\_aligntest"
f = sys.argv[1] if len(sys.argv) > 1 else "auth.py"
src = open(tmp + "\\" + f, encoding="utf-8").read().split("\n")
for i, l in enumerate(src):
    s = l.strip()
    if "logger.exception" in l or 'logger.warning("optional' in l or (s.startswith("except") and " as e" in l):
        print(f"{i+1}: {l}")
