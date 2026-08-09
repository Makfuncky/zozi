import os, subprocess, re

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
ROUTERS = os.path.join(ROOT, "backend", "routers")

out = subprocess.check_output(
    ["git", "-C", ROOT, "ls-tree", "-r", "--name-only", "HEAD", "--", "backend/routers"],
    text=True,
)
git_names = set()
for line in out.splitlines():
    m = re.match(r"^backend/routers/([^/]+\.py)$", line)
    if m and m.group(1) != "__init__.py":
        git_names.add(m.group(1)[:-3])

new_names = set()
for f in os.listdir(ROUTERS):
    if f.endswith(".py") and f != "__init__.py":
        new_names.add(f[:-3])

ADDED_SURFACES = ("public_", "customer_")
OPS = {"access","management","governance","billing","controller","versioning",
       "api","registry","configuration","orchestration","integration","moderation",
       "conversion","automation","monitoring","reconciliation","resolution","scheduling",
       "hierarchy","relocation","insights","ranking","escalation","mediation","dispatch",
       "provisioning","administration","interaction","diagnostics","onboarding",
       "categorization","tracking","fulfillment","fallback","pipeline","audit"}

def reconstruct(n):
    if n in git_names:
        return n
    op = None
    toks = n.split("_")
    if toks[-1] in OPS:
        op = toks[-1]
        core = "_".join(toks[:-1])
    else:
        core = n
    for sp in ADDED_SURFACES:
        if core.startswith(sp):
            core = core[len(sp):]
            break
    return core

mapping = {}
unrecognized = []
for n in sorted(new_names):
    old = reconstruct(n)
    mapping[n] = old
    if n not in git_names and n.split("_")[-1] not in OPS:
        unrecognized.append(n)

rows = []
for new in sorted(mapping):
    old = mapping[new]
    status = "UNCHANGED" if old == new else "RENAMED"
    rows.append((old, new, status))

with open(os.path.join(ROOT, "_extra_files", "rn1_mapping.csv"), "w") as fh:
    fh.write("Old-Name,New-Name,Status\n")
    for old, new, status in rows:
        fh.write(f"{old},{new},{status}\n")

renamed = [r for r in rows if r[2] == "RENAMED"]
unchanged = [r for r in rows if r[2] == "UNCHANGED"]
print(f"disk total={len(new_names)} git total={len(git_names)}")
print(f"RENAMED={len(renamed)} UNCHANGED={len(unchanged)}")
print("UNRECOGNIZED (new not in git, last token not an op):", unrecognized)
print("\n--- RENAMED ---")
for old, new, _ in renamed:
    print(f"{old} -> {new}")
print("\n--- UNCHANGED ---")
for old, new, _ in unchanged:
    print(f"{new}")
