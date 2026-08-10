"""Scan which symbols importers pull from the controllers.admin_controller facade."""
import glob
import re
from collections import Counter

imports = Counter()
for path in glob.glob("backend/**/*.py", recursive=True):
    if "__pycache__" in path or "venv" in path or "backend/controllers/admin" in path:
        continue
    src = open(path, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r"from controllers\.admin_controller import ([^\n]+)", src):
        names = m.group(1).replace("(", ",").replace(")", ",")
        for n in names.split(","):
            n = n.strip().split(" as ")[0].strip()
            if n and n != chr(92):
                imports[n] += 1

print("total importer files:", len(glob.glob("backend/**/*.py", recursive=True)))
for name, cnt in imports.most_common(40):
    print(f"{cnt:3d}  {name}")
