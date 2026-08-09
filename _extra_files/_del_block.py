import os
root = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
p = os.path.join(root, "backend", "middleware", "country_context.py")
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
before = len(lines)
# delete lines 181..234 inclusive (1-indexed) -> slice [180:234]
del lines[180:234]
with open(p, "w", encoding="utf-8") as f:
    f.writelines(lines)
print("removed", before - len(lines), "lines; now", len(lines))
