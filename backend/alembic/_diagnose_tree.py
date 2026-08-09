"""Diagnose the Alembic migration tree — find duplicates, branches, heads."""
import os, re
from collections import defaultdict

versions_dir = os.path.join(os.path.dirname(__file__), "versions")
rev_map = {}       # revision -> (filename, down_revision, message)
down_map = defaultdict(list)  # down_revision -> [revision_id]

for f in sorted(os.listdir(versions_dir)):
    if not f.endswith(".py") or f == "__init__.py":
        continue
    path = os.path.join(versions_dir, f)
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    rev_m = re.search(r'revision\s*=\s*["\']([^"\']+)["\']', content)
    down_m = re.search(r'down_revision\s*=\s*["\']([^"\']*)["\']', content)
    msg_m = re.search(r'message\s*=\s*["\']([^"\']*)["\']', content)
    if not rev_m:
        continue
    rev_id = rev_m.group(1)
    down_rev = down_m.group(1) if down_m and down_m.group(1) else None
    message = msg_m.group(1) if msg_m else f.replace(".py", "")
    if rev_id in rev_map:
        prev_f, prev_down, prev_msg = rev_map[rev_id]
        print(f"DUPLICATE REVISION: {rev_id}")
        print(f"  File 1: {prev_f}  (down={prev_down})  msg={prev_msg}")
        print(f"  File 2: {f}  (down={down_rev})  msg={message}")
    else:
        rev_map[rev_id] = (f, down_rev, message)
    if down_rev:
        down_map[down_rev].append(rev_id)

total_files = len([f for f in os.listdir(versions_dir) if f.endswith(".py") and f != "__init__.py"])
print(f"Total unique revisions: {len(rev_map)}")
print(f"Total files: {total_files}")
print(f"Duplicates: {total_files - len(rev_map)}")

roots = [r for r, (_, down, _) in rev_map.items() if down is None]
print(f"\nRoots (down=None): {roots}")

all_children = set()
for children in down_map.values():
    all_children.update(children)
heads = set(rev_map.keys()) - all_children
print(f"\nHeads ({len(heads)}):")
for h in sorted(heads):
    f, down, msg = rev_map[h]
    print(f"  {h}: {msg[:70]}")

# Branches (one parent -> multiple children)
print(f"\nBranches (one parent -> multiple children):")
for down_rev, children in sorted(down_map.items()):
    if len(children) > 1:
        parent_info = rev_map.get(down_rev, (None, None, "UNKNOWN"))
        print(f"  {down_rev} ({parent_info[2][:50]}) -> {len(children)} children:")
        for c in children:
            info = rev_map.get(c, ("", "", ""))
            print(f"    -> {c}: {info[2][:50]}")

# Stubs
print(f"\nStub files:")
for f in sorted(os.listdir(versions_dir)):
    if f.startswith("s_") and f.endswith(".py"):
        with open(os.path.join(versions_dir, f), encoding="utf-8") as fh:
            content = fh.read()
        rev_m = re.search(r'revision\s*=\s*["\']([^"\']+)["\']', content)
        msg_m = re.search(r'message\s*=\s*["\']([^"\']*)["\']', content)
        if rev_m and msg_m:
            print(f"  {rev_m.group(1)}: {msg_m.group(1)[:60]}")
