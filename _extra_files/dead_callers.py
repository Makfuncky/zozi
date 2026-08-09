import os, re, json

base = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
d = json.load(open(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\w1_w4_scan.json"))
callers = set(e["module"] for e in d["w4"])

mod_re = re.compile(r"^\s*(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))")
imports_all = []  # (module_imported, filepath)
for root, _, files in os.walk(base):
    rp = root.replace("\\", "/")
    if "/tests" in rp or rp.endswith("/tests"):
        continue
    for fn in files:
        if not fn.endswith(".py"):
            continue
        fp = os.path.join(root, fn)
        try:
            with open(fp, encoding="utf-8-sig", errors="ignore") as f:
                for ln in f:
                    m = mod_re.match(ln)
                    if m:
                        imports_all.append((m.group(1) or m.group(2), fp))
        except Exception:
            pass

inbound = {c: 0 for c in callers}
for imp, fp in imports_all:
    for c in callers:
        if imp == c or imp.startswith(c + "."):
            inbound[c] += 1
            break

for c in sorted(callers):
    p = os.path.join(base, *c.split(".")) + ".py"
    exists = os.path.exists(p)
    print(f"{c:48} exists={exists} inbound_imports={inbound[c]}")
