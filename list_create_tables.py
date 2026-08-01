import os
import re

root = "backend/alembic/versions"
for f in sorted(os.listdir(root)):
    if not f.endswith(".py"):
        continue
    src = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
    names = re.findall(r'op\.create_table\(\s*["\']([^"\']+)["\']', src)
    drops = re.findall(r'op\.drop_table\(\s*["\']([^"\']+)["\']', src)
    if names or drops:
        print(f"{f}: create=[{','.join(names)}] drop=[{','.join(drops)}]")
