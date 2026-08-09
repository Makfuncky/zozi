import os, re

base = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

def mod_of(path):
    rel = os.path.relpath(path, base).replace("\\", "/")[:-3]  # drop .py
    return rel.replace("/", ".")

mod_re = re.compile(r"^\s*(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))")
edges = []  # (caller_module, target_module, filepath)
imports_index = []  # (imported_module, filepath)

for root, _, files in os.walk(base):
    rp = root.replace("\\", "/")
    if "/tests" in rp or rp.endswith("/tests"):
        continue
    for fn in files:
        if not fn.endswith(".py"):
            continue
        fp = os.path.join(root, fn)
        caller = mod_of(fp)
        try:
            with open(fp, encoding="utf-8-sig", errors="ignore") as f:
                for ln in f:
                    m = mod_re.match(ln)
                    if not m:
                        continue
                    imp = m.group(1) or m.group(2)
                    imports_index.append((imp, fp))
                    if caller.startswith("controllers.") and imp.startswith("controllers.") and imp != "controllers":
                        edges.append((caller, imp, fp))
        except Exception:
            pass

callers = {}
for c, t, fp in edges:
    callers.setdefault(c, set()).add(t)

inbound = {c: 0 for c in callers}
for imp, fp in imports_index:
    for c in callers:
        if imp == c or imp.startswith(c + "."):
            inbound[c] += 1
            break

print("=== DEAD legacy controllers (inbound==0, exists) ===")
dead = []
for c in sorted(callers):
    p = os.path.join(base, *c.split(".")) + ".py"
    exists = os.path.exists(p)
    if exists and inbound[c] == 0:
        dead.append(c)
        print(f"DEAD  {c:48} targets={sorted(callers[c])}")
print()
print(f"total callers={len(callers)} dead_candidates={len(dead)}")
