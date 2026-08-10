import os, re, json, subprocess

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
ROUTERS = os.path.join(BACKEND, "routers")
BAK = os.path.abspath(os.path.join(os.path.dirname(__file__), "_router_backup_before_rename"))

rev = json.load(open(os.path.join(BAK, "reverse_map.json"), encoding="utf-8"))  # new -> old

files = sorted(f for f in os.listdir(ROUTERS) if f.endswith(".py") and f != "__init__.py")

def route_count(text):
    return len(re.findall(r"@\w*router\.(get|post|put|delete|patch|websocket)", text))

def git_show(path):
    try:
        out = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=BACKEND,
                             capture_output=True, text=True)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout
    except Exception:
        pass
    return None

restorable = []
unrecoverable = []
for f in files:
    text = open(os.path.join(ROUTERS, f), encoding="utf-8").read()
    if route_count(text) > 0:
        continue  # already has routes
    stem = f[:-3]
    old = rev.get(stem)
    orig = None
    if old:
        orig = git_show(f"backend/routers/{old}.py")
    if not orig:
        orig = git_show(f"backend/routers/{f}")
    if orig and route_count(orig) > 0:
        restorable.append((stem, old, route_count(orig)))
    else:
        unrecoverable.append(stem)

print(f"RESTORABLE from git (had real routes): {len(restorable)}")
print(f"UNRECOVERABLE (no git original w/ routes): {len(unrecoverable)}")
print()
print("UNRECOVERABLE list:")
for s in unrecoverable:
    print("  ", s)
