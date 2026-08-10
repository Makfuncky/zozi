import os, re, sys, json, importlib

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
BACKEND = os.path.join(ROOT, "backend")
MAIN = os.path.join(BACKEND, "main.py")
mapping = json.load(open(os.path.join(ROOT, "_extra_files", "final_rename_map.json"), encoding="utf-8"))
renames = {o[:-3]: n for o, n in mapping.items() if o[:-3] != n}

sys.path.insert(0, BACKEND)
txt = open(MAIN, encoding="utf-8", errors="ignore").read()
# extract router_names tuple pairs (name, path)
pairs = re.findall(r'\(\s*["\']([a-zA-Z0-9_]+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)', txt)

results = []
for name, path in pairs:
    try:
        importlib.import_module("routers." + name)
        results.append((name, "OK"))
    except Exception as e:
        results.append((name, f"FAIL:{type(e).__name__}:{str(e)[:60]}"))

# which renamed-live routers fail?
renamed_live = [n for o, n in renames.items() if any(p[0] == n for p in pairs)]
print("Renamed modules that are registered in router_names:", len(renamed_live))
for name in renamed_live:
    st = next((r[1] for r in results if r[0] == name), "NOT IN LIST")
    print(f"  {name:<42} {st}")

fails = [(n, s) for n, s in results if not s.startswith("OK")]
print("\nTOTAL registered names:", len(pairs))
print("TOTAL failing:", len(fails))
for n, s in fails:
    print("  FAIL", n, s)
