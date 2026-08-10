import os, re, json, shutil

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
ROUTERS = os.path.join(ROOT, "backend", "routers")
MAIN = os.path.join(ROOT, "backend", "main.py")

mapping = json.load(open(os.path.join(ROOT, "_extra_files", "final_rename_map.json"), encoding="utf-8"))
# old_stem -> new_stem (only actual renames)
renames = {o[:-3]: n for o, n in mapping.items() if o[:-3] != n}
print("renames to perform:", len(renames))

# ---- 0. BACKUP (reversible) ----
backup = os.path.join(ROOT, "_extra_files", "_router_backup_before_rename")
if os.path.exists(backup):
    shutil.rmtree(backup)
def ignore_pyc(dirpath, names):
    return {n for n in names if n == "__pycache__"}
shutil.copytree(ROUTERS, backup, ignore=ignore_pyc)
shutil.copy(MAIN, os.path.join(backup, "main.py"))
json.dump({v: k for k, v in renames.items()}, open(os.path.join(backup, "reverse_map.json"), "w"), indent=2)
print("backup written to", backup)

# ---- 1. RENAME FILES ----
missing = []
for old, n in renames.items():
    src = os.path.join(ROUTERS, old + ".py")
    dst = os.path.join(ROUTERS, n + ".py")
    if os.path.exists(src):
        os.rename(src, dst)
    else:
        missing.append(old)
print("renamed on disk; missing:", missing)

# remove stale pyc for renamed modules
for old in list(renames):
    pyc = os.path.join(ROUTERS, "__pycache__", old + ".cpython-*.pyc")
for dp, dn, fn in os.walk(os.path.join(ROUTERS, "__pycache__")):
    for f in fn:
        stem = f.split(".")[0]
        if stem in renames:
            try: os.remove(os.path.join(dp, f))
            except: pass

# ---- 2. REWIRE REFERENCES ----
pairs = sorted(renames.items(), key=lambda kv: len(kv[0]), reverse=True)

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

edited = []
for path in scan_files():
    try:
        txt = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        continue
    new_txt = txt
    for old, n in pairs:
        for pat in [r"(backend\.routers\.)" + re.escape(old) + r"\b",
                    r"(routers\.)" + re.escape(old) + r"\b"]:
            new_txt = re.sub(pat, lambda m, n=n: m.group(1) + n, new_txt)
    # main.py router_names tuple string literals
    if os.path.basename(path) == "main.py":
        for old, n in pairs:
            new_txt = re.sub(r'("' + re.escape(old) + r'"|\'' + re.escape(old) + r'\'")', '"' + n + '"', new_txt)
    if new_txt != txt:
        open(path, "w", encoding="utf-8").write(new_txt)
        edited.append(path)

print("files edited (references):", len(edited))
for p in edited:
    print("  ", os.path.relpath(p, ROOT))

# ---- 3. VERIFY: no dangling old-module references remain ----
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
# also check main.py quoted tuples
mtxt = open(MAIN, encoding="utf-8", errors="ignore").read()
for old in renames:
    if re.search(r'["\']' + re.escape(old) + r'["\']', mtxt):
        dangling.append(("backend/main.py", old))

print("\nDANGLING REFERENCES:", len(dangling))
for d in dangling:
    print("  ", d)

# compile all backend .py
import py_compile
bad = []
for path in scan_files():
    try:
        py_compile.compile(path, doraise=True)
    except Exception as e:
        bad.append((os.path.relpath(path, ROOT), str(e)[:80]))
print("\nCOMPILE ERRORS:", len(bad))
for b in bad:
    print("  ", b)
