import os, re
ROOT = os.getcwd()
MARKER = "AUTO-GENERATED"
decorated = set()
for dp, _, fs in os.walk("controllers"):
    for fn in fs:
        if not fn.endswith(".py") or fn == "__init__.py":
            continue
        p = os.path.join(dp, fn)
        try:
            t = open(p, encoding="utf-8").read()
        except Exception:
            continue
        if re.search(r"from (?:routers\.generated\.)?auto_router import|from core\.route_contract import", t):
            mod = os.path.relpath(p, ROOT)[:-3].replace(os.sep, ".")
            decorated.add(mod)
hw = []
for dp, _, fs in os.walk("routers"):
    for fn in fs:
        if not fn.endswith(".py") or fn == "__init__.py":
            continue
        p = os.path.join(dp, fn)
        try:
            t = open(p, encoding="utf-8").read()
        except Exception:
            continue
        if MARKER in t:
            continue
        ctrls = set(re.findall(r"from (controllers\.[A-Za-z0-9_.]+) import", t))
        hit = [c for c in ctrls if c in decorated]
        hw.append((fn, sorted(ctrls), sorted(hit)))
conv = [h for h in hw if h[2]]
print(f"decorated controllers: {len(decorated)}")
print(f"hand-written routers: {len(hw)}")
print(f"hand-written routers importing a DECORATED controller: {len(conv)}")
for fn, ctrls, hit in conv[:80]:
    print(f"  {fn} -> {hit}")
