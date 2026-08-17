import importlib, os, sys, threading, re

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
sys.path.insert(0, ROOT)
EXCLUDE = {"venv", "__pycache__", ".git", "node_modules", "tests", "alembic"}

def iter_modules():
    for dirpath, dirs, files in os.walk(ROOT):
        relparts = set(os.path.relpath(dirpath, ROOT).split(os.sep))
        if relparts & EXCLUDE:
            dirs[:] = []
            continue
        for f in files:
            if not f.endswith(".py") or f == "__init__.py":
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, ROOT)[:-3].replace(os.sep, ".")
            yield rel

def worker(mod, out):
    try:
        importlib.import_module(mod)
        out.append(("OK", ""))
    except ImportError as e:
        out.append(("IMPORTERROR", str(e)))
    except Exception as e:
        out.append(("OTHER", type(e).__name__ + ": " + str(e)[:150]))

imp = {}  # mod -> msg
for mod in sorted(iter_modules()):
    out = []
    t = threading.Thread(target=worker, args=(mod, out), daemon=True)
    t.start()
    t.join(3.0)
    if t.is_alive():
        continue
    if out and out[0][0] == "IMPORTERROR":
        imp[mod] = out[0][1]

# Parse "cannot import name 'X' from 'Y'" and "No module named 'Y'"
re_name = re.compile(r"cannot import name '([^']+)' from '([^']+)'")
re_mod = re.compile(r"No module named '([^']+)'")

from collections import defaultdict
groups = defaultdict(list)   # (target, name) -> [importer modules]
unresolved_mod = defaultdict(list)

for mod, msg in imp.items():
    m1 = re_name.search(msg)
    if m1:
        groups[(m1.group(2), m1.group(1))].append(mod)
        continue
    m2 = re_mod.search(msg)
    if m2:
        unresolved_mod[m2.group(1)].append(mod)

print("TOTAL IMPORTERROR MODULES:", len(imp))
print("=" * 90)
print("## A) cannot import name 'X' from 'Y'  (real wiring breaks)")
print("=" * 90)
for (tgt, name), importers in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0][1])):
    print(f"\n### MISSING: {name}  FROM: {tgt}   ({len(importers)} importers)")
    for im in importers:
        print(f"   - {im}")

print("\n" + "=" * 90)
print("## B) No module named 'Y'  (intermediate module missing)")
print("=" * 90)
for modname, importers in sorted(unresolved_mod.items(), key=lambda kv: (-len(kv[1]), kv[0])):
    print(f"\n### MISSING MODULE: {modname}   ({len(importers)} importers)")
    for im in importers[:10]:
        print(f"   - {im}")
    if len(importers) > 10:
        print(f"   ... +{len(importers)-10} more")
