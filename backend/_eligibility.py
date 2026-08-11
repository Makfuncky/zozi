"""Analyze which plain controllers are eligible for auto-router migration.

Eligibility:
 1. single surface (all routes share one SURFACES prefix)
 2. referenced by exactly ONE hand-written router
 3. controller body has no db.commit()/session.commit()/flush
 4. controller does NOT define its own router (already filtered = "plain")
 5. safe to change signature (callers only routers/tests, checked separately)
"""
from __future__ import annotations
import ast, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTROLLERS = os.path.join(ROOT, "controllers")
ROUTERS = os.path.join(ROOT, "routers")

SURFACES = {
    "admin": "/api/v1/admin",
    "customer": "/api/v1/customer",
    "supplier": "/api/v1/supplier",
    "logistics": "/api/v1/logistics",
    "public": "/api/v1",
    "system": "/api/v1/system",
    "internal": "/api/v1/internal",
}

def surface_for(path):
    best = None
    for n, p in SURFACES.items():
        if path.startswith(p) and (best is None or len(p) > len(best[1])):
            best = (n, p)
    return best

def call_target(tree):
    """Find the controller function name called in wrapper bodies (return/await some_func(...))."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Return, ast.Expr)):
            val = node.value
            if isinstance(val, ast.Await):
                val = val.value
            # could be return some_func(...) or await some_func(...)
            if isinstance(val, ast.Call) and isinstance(val.func, ast.Name):
                names.add(val.func.id)
            # return {"x": f(...)} etc unlikely
    return names

def analyze_router(fp):
    text = open(fp, encoding="utf-8").read()
    if "AUTO-GENERATED" in text:
        return None
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    prefix = ""
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == "router":
                    for kw in (n.value.keywords if isinstance(n.value, ast.Call) else []):
                        if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                            prefix = kw.value.value
    routes = []
    imported_controller_funcs = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        meta = None
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in ("get","post","put","patch","delete"):
                method = dec.func.attr.upper()
                path = None
                if dec.args:
                    if isinstance(dec.args[0], ast.Constant):
                        path = dec.args[0].value
                for kw in dec.keywords:
                    if kw.arg == "path" and isinstance(kw.value, ast.Constant):
                        path = kw.value.value
                if path is None:
                    path = ""
                meta = {"method": method, "path": prefix + path, "func": node.name}
                break
        if not meta:
            continue
        # find controller func called
        for cn in call_target(node):
            imported_controller_funcs.add(cn)
        routes.append(meta)
    if not routes:
        return None
    return {"prefix": prefix, "routes": routes, "calls": imported_controller_funcs, "file": fp}

def controller_funcs(fp):
    text = open(fp, encoding="utf-8").read()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(n.name)
    return names

def body_has_commit(fp):
    text = open(fp, encoding="utf-8").read()
    if re.search(r"\b(db|session)\.(commit|flush)\b", text):
        return True
    return False

def main():
    # index routers
    routers = []
    for fn in os.listdir(ROUTERS):
        if not fn.endswith(".py") or fn == "__init__.py":
            continue
        a = analyze_router(os.path.join(ROUTERS, fn))
        if a:
            routers.append(a)

    plain = []
    for dirpath, _, files in os.walk(CONTROLLERS):
        for fn in files:
            if not fn.endswith(".py") or fn == "__init__.py":
                continue
            fp = os.path.join(dirpath, fn)
            text = open(fp, encoding="utf-8").read()
            if "from routers.generated.auto_router import" in text:
                continue
            if re.search(r"router\s*=\s*APIRouter", text):
                continue
            rel = os.path.relpath(fp, ROOT)[:-3].replace(os.sep, ".")
            plain.append((rel, fp))

    for rel, fp in plain:
        cfuncs = controller_funcs(fp)
        referencing = []
        for r in routers:
            if r["calls"] & cfuncs:
                # only count if at least one route actually maps to this controller's funcs
                referencing.append(r)
        # check single router reference (only routers whose calls are subset of cfuncs? we want routers that wrap THIS controller)
        # A router may wrap multiple controllers; criterion: controller referenced by exactly ONE router.
        if len(referencing) != 1:
            continue
        r = referencing[0]
        # all routes' called funcs must belong to this controller (router exclusively wraps this controller)
        if not (r["calls"] <= cfuncs):
            continue
        # surface check
        surfs = {surface_for(rt["path"]) for rt in r["routes"]}
        surfs.discard(None)
        if len(surfs) != 1:
            continue
        # commit/flush check
        if body_has_commit(fp):
            continue
        print(f"ELIGIBLE: {rel}")
        print(f"  router: {os.path.basename(r['file'])}  prefix={r['prefix']}  surface={list(surfs)[0][0]}")
        for rt in r["routes"]:
            print(f"    {rt['method']:7} {rt['path']}  -> {rt['func']}")

if __name__ == "__main__":
    main()
