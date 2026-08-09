import os, re, glob
root = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\models"
pat = re.compile(r"from \.([\w\.]+) import \*")
missing = []
for init in glob.glob(os.path.join(root, "**", "__init__.py"), recursive=True) + [os.path.join(root, "_exports.py")]:
    d = os.path.dirname(init)
    with open(init, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            m = pat.search(line)
            if not m:
                continue
            rel = m.group(1)
            # resolve relative to package dir d
            parts = rel.split(".")
            target_dir = d
            mod = parts[-1]
            sub = parts[:-1]
            for s in sub:
                target_dir = os.path.join(target_dir, s)
            cand = os.path.join(target_dir, mod + ".py")
            if not os.path.exists(cand):
                missing.append((os.path.relpath(init, root), ln, rel, cand))
for x in missing:
    print("MISSING:", x[0], "line", x[1], "->", x[2])
print("TOTAL MISSING:", len(missing))
