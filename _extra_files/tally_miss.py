import json, re
from collections import Counter

d = json.load(open(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\boot_probe.json", encoding="utf-8"))
miss = Counter()
for f in d["failed"]:
    e = f["error"]
    m = re.search(r"cannot import name '(\w+)' from '([\w.]+)'", e)
    if m:
        miss[(m.group(1), m.group(2))] += 1
print("UNIQUE (symbol, target_module) pairs:", len(miss))
print()
for (sym, mod), c in sorted(miss.items(), key=lambda x: -x[1]):
    print(f"{c:3d}  {sym:42s} <- {mod}")
