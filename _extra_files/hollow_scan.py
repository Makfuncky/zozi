import os, re

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
ROUTERS = os.path.join(BACKEND, "routers")

files = sorted(f for f in os.listdir(ROUTERS) if f.endswith(".py") and f != "__init__.py")

decorator = re.compile(r"@\w*router\.(get|post|put|delete|patch|websocket)")
prog_wire = re.compile(r"include_router|add_api_route|public_router\s*=")

hollow = []
non_hollow_empty = []
for f in files:
    text = open(os.path.join(ROUTERS, f), encoding="utf-8").read()
    has_decorator = bool(decorator.search(text))
    has_prog = bool(prog_wire.search(text))
    if not has_decorator and not has_prog:
        hollow.append(f)
    elif not has_decorator and has_prog:
        non_hollow_empty.append(f)

print("HOLLOW (no routes at all):", len(hollow))
print("EMPTY-but-has-programmatic-wiring (DO NOT overwrite):", len(non_hollow_empty))
for f in non_hollow_empty:
    print("   ", f)
