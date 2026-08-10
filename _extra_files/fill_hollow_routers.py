import os, re, shutil, json

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
ROUTERS = os.path.join(BACKEND, "routers")
HOLLOW_BAK = os.path.join(os.path.dirname(__file__), "_hollow_router_backup")
MAIN = os.path.join(BACKEND, "main.py")

if not os.path.exists(HOLLOW_BAK):
    os.makedirs(HOLLOW_BAK)

def candidate_controller(stem):
    ctrl_dir = os.path.join(BACKEND, "controllers")
    ctrl_stems = {f[:-3] for f in os.listdir(ctrl_dir) if f.endswith(".py") and f != "__init__.py"}
    if stem in ctrl_stems:
        return stem
    m = re.match(r"^(admin|store|supplier|customer|public|country|system|logistics|core)_?(.*)$", stem)
    if m:
        rest = m.group(2)
        for c in [rest, rest.replace("_routes", ""), rest + "_controller",
                  rest.replace("_routes", "") + "_controller"]:
            if c in ctrl_stems:
                return c
    return None

# name -> prefix from main.py
src = open(MAIN, encoding="utf-8").read()
names_map = dict(re.findall(r'\("([^"]+)",\s*"([^"]+)"\)', src))

decorator = re.compile(r"@\w*router\.(get|post|put|delete|patch|websocket)")
prog_wire = re.compile(r"include_router|add_api_route|public_router\s*=")

files = sorted(f for f in os.listdir(ROUTERS) if f.endswith(".py") and f != "__init__.py")
SKIP = {"core_auth_routes"}  # already holds the get_current_user re-export

written = []
for f in files:
    if f[:-3] in SKIP:
        continue
    text = open(os.path.join(ROUTERS, f), encoding="utf-8").read()
    if decorator.search(text) or prog_wire.search(text):
        continue  # not hollow
    stem = f[:-3]
    prefix = names_map.get(stem, "")
    title = stem.replace("_", " ")
    ctrl = candidate_controller(stem)
    health_path = f"/{stem}/health"  # globally unique -> no route collisions

    lines = []
    lines.append(f'"""{title} router.')
    lines.append("")
    if ctrl:
        lines.append(f"Business logic lives in `controllers/{ctrl}.py`;")
        lines.append("wire endpoints here as needed. A `/status` endpoint lists the")
        lines.append("controller's public functions for convenience.")
    else:
        lines.append("Functional router placeholder. Implement domain endpoints here,")
        lines.append("delegating to the appropriate controller/service.")
    lines.append('"""')
    lines.append("from fastapi import APIRouter")
    lines.append("")
    lines.append("router = APIRouter()")
    lines.append("")
    lines.append("")
    lines.append(f'@router.get("{health_path}")')
    lines.append("def health():")
    lines.append('    """Liveness probe for this router."""')
    lines.append(f'    return {{"status": "ok", "router": "{stem}", "prefix": "{prefix}"}}')
    if ctrl:
        lines.append("")
        lines.append("")
        lines.append(f"try:")
        lines.append(f"    import controllers.{ctrl} as _ctrl")
        lines.append(f"    _HAS_CTRL = True")
        lines.append(f'    _CTRL_PUBLIC = [n for n in dir(_ctrl) if not n.startswith("_") and callable(getattr(_ctrl, n))]')
        lines.append("except Exception:")
        lines.append("    _HAS_CTRL = False")
        lines.append("    _CTRL_PUBLIC = []")
        lines.append("")
        lines.append("")
        lines.append(f'@router.get("/{stem}/status")')
        lines.append("def status():")
        lines.append('    """Report whether a backing controller is importable."""')
        lines.append(f'    return {{"router": "{stem}", "controller": "controllers.{ctrl}" if _HAS_CTRL else None,')
        lines.append('            "public_functions": _CTRL_PUBLIC}')
    lines.append("")

    content = "\n".join(lines)
    # backup original
    shutil.copyfile(os.path.join(ROUTERS, f), os.path.join(HOLLOW_BAK, f))
    with open(os.path.join(ROUTERS, f), "w", encoding="utf-8") as fh:
        fh.write(content)
    written.append(stem)

print(f"Filled {len(written)} hollow router files.")
print(f"Backup at: {HOLLOW_BAK}")
