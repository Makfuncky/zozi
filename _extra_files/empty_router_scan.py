import os, re

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
ROUTERS = os.path.join(BACKEND, "routers")
CTRL = os.path.join(BACKEND, "controllers")

files = sorted(f for f in os.listdir(ROUTERS) if f.endswith(".py") and f != "__init__.py")
ctrl_stems = {f[:-3] for f in os.listdir(CTRL) if f.endswith(".py") and f != "__init__.py"}

empty = []
with_routes = []
for f in files:
    text = open(os.path.join(ROUTERS, f), encoding="utf-8").read()
    routes = re.findall(r"@\w*router\.(get|post|put|delete|patch|websocket)", text)
    if not routes:
        empty.append(f)
    else:
        with_routes.append((f, len(routes)))

print(f"Total router files : {len(files)}")
print(f"With routes        : {len(with_routes)}")
print(f"EMPTY (no routes)  : {len(empty)}")
print()

# For each empty file, can we find a candidate controller module?
def candidate_controller(stem):
    # direct match
    if stem in ctrl_stems:
        return stem
    # strip surface prefix (admin_, store_, supplier_, customer_, public_, country_, system_, logistics_, core_)
    m = re.match(r"^(admin|store|supplier|customer|public|country|system|logistics|core)_?(.*)$", stem)
    if m:
        rest = m.group(2)
        # try rest as controller name, or rest + _controller, or with trailing _routes/_create etc.
        cands = [rest, rest.replace("_routes", ""), rest + "_controller",
                 rest.replace("_routes", "") + "_controller"]
        for c in cands:
            if c in ctrl_stems:
                return c
    return None

has_ctrl = []
no_ctrl = []
for f in empty:
    stem = f[:-3]
    c = candidate_controller(stem)
    if c:
        has_ctrl.append((stem, c))
    else:
        no_ctrl.append(stem)

print(f"EMPTY files WITH a candidate controller: {len(has_ctrl)}")
for s, c in has_ctrl:
    print(f"  {s:40s} -> controllers/{c}.py")
print()
print(f"EMPTY files WITHOUT a candidate controller: {len(no_ctrl)}")
for s in no_ctrl:
    print(f"  {s}")
