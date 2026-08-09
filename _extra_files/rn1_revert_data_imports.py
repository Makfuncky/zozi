import os, re

backend = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
pairs = [
    (r'from data\.services import', 'from services import'),
    (r'import data\.services', 'import services'),
    (r'from data\.db import', 'from db.database import'),
    (r'import data\.db', 'import db.database'),
]
compiled = [(re.compile(a), b) for a, b in pairs]

changed = 0
for root, dirs, files in os.walk(backend):
    if "venv" in root.split(os.sep):
        continue
    for fn in files:
        if not fn.endswith(".py"):
            continue
        p = os.path.join(root, fn)
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except Exception:
            continue
        new = text
        for rx, rep in compiled:
            new = rx.sub(rep, new)
        if new != text:
            with open(p, "w", encoding="utf-8") as f:
                f.write(new)
            changed += 1
            print("reverted", os.path.relpath(p, backend))
print("TOTAL FILES REVERTED:", changed)
