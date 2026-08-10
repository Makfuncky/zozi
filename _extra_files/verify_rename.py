import os, re, json, py_compile

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
ROUTERS = os.path.join(ROOT, "backend", "routers")
MAIN = os.path.join(ROOT, "backend", "main.py")
mapping = json.load(open(os.path.join(ROOT, "_extra_files", "final_rename_map.json"), encoding="utf-8"))
renames = {o[:-3]: n for o, n in mapping.items() if o[:-3] != n}

def scan_files():
    for dp, dn, fn in os.walk(os.path.join(ROOT, "backend")):
        parts = dp.split(os.sep)
        if "scripts" in parts:
            continue
        if os.path.basename(dp) == "__pycache__":
            continue
        for f in fn:
            if f.endswith(".py"):
                yield os.path.join(dp, f)

dangling = []
for path in scan_files():
    try:
        txt = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        continue
    for old in renames:
        for pat in [r"backend\.routers\." + re.escape(old) + r"\b",
                    r"routers\." + re.escape(old) + r"\b"]:
            if re.search(pat, txt):
                dangling.append((os.path.relpath(path, ROOT), old))
mtxt = open(MAIN, encoding="utf-8", errors="ignore").read()
for old in renames:
    if re.search(r'["\']' + re.escape(old) + r'["\']', mtxt):
        dangling.append(("backend/main.py", old))

print("DANGLING REFERENCES:", len(dangling))
for d in dangling:
    print("  ", d)

# compile routers + main only (fast, targeted)
bad = []
for base in scan_files():
    if base == ROUTERS or os.path.dirname(base) == ROUTERS or os.path.basename(base) == "main.py":
        try:
            py_compile.compile(base, doraise=True)
        except Exception as e:
            bad.append((os.path.relpath(base, ROOT), str(e)[:100]))
print("COMPILE ERRORS (routers+main):", len(bad))
for b in bad:
    print("  ", b)

# confirm all new files exist, all old gone
missing_new = [o for o, n in renames.items() if not os.path.exists(os.path.join(ROUTERS, n + ".py"))]
still_old = [o for o in renames if os.path.exists(os.path.join(ROUTERS, o + ".py"))]
print("MISSING NEW FILES:", missing_new)
print("OLD FILES STILL PRESENT:", still_old)
print("TOTAL routers now:", len([f for f in os.listdir(ROUTERS) if f.endswith('.py') and f!='__init__.py']))
