import os, re
from collections import defaultdict

revs = defaultdict(list)
for f in sorted(os.listdir("alembic/versions")):
    if not f.endswith(".py") or f == "__init__.py":
        continue
    path = os.path.join("alembic/versions", f)
    with open(path) as fh:
        content = fh.read()
    rev = re.search(r"revision\s*=\s*['\"]([^'\"]+)['\"]", content)
    down = re.search(r"down_revision\s*=\s*['\"]([^'\"]+)['\"]", content)
    if rev:
        revs[rev.group(1)].append(f)
        dc = down.group(1) if down else "None"
        # Check for duplicate revisions
        if len(revs[rev.group(1)]) > 1:
            print(f"  DUPLICATE REVISION: {rev.group(1)}")

print(f"\nTotal unique revisions: {len(revs)}")
print(f"Total files: {sum(len(v) for v in revs.values())}")

# Check which revision points to what
head = None
for rev_id, files in revs.items():
    path = os.path.join("alembic/versions", files[0])
    with open(path) as fh:
        content = fh.read()
    down = re.search(r"down_revision\s*=\s*['\"]([^'\"]+)['\"]", content)
    if down:
        dc = down.group(1)
        if dc == "None" or dc is None:
            head = rev_id
print(f"\nBase revision (down_revision=None): {head}")

