import os, subprocess, re

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
ROUTERS = os.path.join(ROOT, "backend", "routers")

# Old names from git HEAD
out = subprocess.check_output(
    ["git", "-C", ROOT, "ls-tree", "-r", "--name-only", "HEAD", "--", "backend/routers"],
    text=True,
)
old_names = set()
for line in out.splitlines():
    m = re.match(r"^backend/routers/([^/]+\.py)$", line)
    if m and m.group(1) != "__init__.py":
        old_names.add(m.group(1)[:-3])

# New names from disk
new_names = set()
for f in os.listdir(ROUTERS):
    if f.endswith(".py") and f != "__init__.py":
        new_names.add(f[:-3])

# Match: exact (unchanged) first, then prefix rename (old + "_" + token)
unchanged = old_names & new_names
renamed_old = old_names - new_names
renamed_new = new_names - old_names

mapping = {}  # new -> old
for n in unchanged:
    mapping[n] = n

# for each renamed old, find new = old + "_" + X
# prefer longest old prefix
remaining_new = set(renamed_new)
for n in sorted(renamed_new, key=len, reverse=True):
    # find all old that are a prefix of n with an extra single token
    cands = [o for o in renamed_old if n == o or n.startswith(o + "_")]
    if cands:
        # longest prefix
        o = max(cands, key=len)
        mapping[n] = o
        renamed_old.discard(o)
        remaining_new.discard(n)

# any new not mapped (e.g., newly created? shouldn't happen)
for n in remaining_new:
    mapping.setdefault(n, n)

# any old not mapped (deleted?)
unmapped_old = renamed_old

rows = []
for new in sorted(mapping):
    old = mapping[new]
    status = "RENAMED" if old != new else ("UNCHANGED" if old in unchanged else "NEW?")
    rows.append((old, new, status))

with open(os.path.join(ROOT, "_extra_files", "rn1_mapping.csv"), "w") as fh:
    fh.write("Old-Name,New-Name,Status\n")
    for old, new, status in rows:
        fh.write(f"{old},{new},{status}\n")

print(f"total new={len(new_names)} total old={len(old_names)}")
print(f"renamed={sum(1 for r in rows if r[2]=='RENAMED')} "
      f"unchanged={sum(1 for r in rows if r[2]=='UNCHANGED')} "
      f"new?={len(remaining_new)} unmapped_old={len(unmapped_old)}")
print("UNMAPPED OLD:", sorted(unmapped_old))
print("UNMAPPED NEW:", sorted(remaining_new))
