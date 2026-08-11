"""Eligibility analyzer: which controllers can be migrated to auto_router shape."""
from __future__ import annotations

import ast
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTROLLERS_DIR = os.path.join(ROOT, "controllers")
ROUTERS_DIR = os.path.join(ROOT, "routers")

API_VERSION_PREFIX = "/api/v1"
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
    for name, p in SURFACES.items():
        if path.startswith(p) and (best is None or len(p) > len(best[1])):
            best = (name, p)
    return best


def find_router_prefix(text):
    m = __import__("re").search(r'APIRouter\(\s*prefix\s*=\s*"([^"]*)"', text)
    return m.group(1) if m else ""


def delegated_call_name(func_node, imported_names):
    """Find the controller function name this router route delegates to."""
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in imported_names:
                return node.func.id
    return None


def analyze_routers():
    """Return dict: controller_module -> list of (router_file, method, full_path, func)."""
    mapping = {}
    for fn in sorted(os.listdir(ROUTERS_DIR)):
        if not fn.endswith(".py") or fn == "__init__.py":
            continue
        fp = os.path.join(ROUTERS_DIR, fn)
        try:
            text = open(fp, encoding="utf-8").read()
            tree = ast.parse(text)
        except Exception:
            continue
        prefix = find_router_prefix(text)
        # imports from controllers.*
        imported = {}  # name -> module
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("controllers"):
                for alias in node.names:
                    imported[alias.asname or alias.name] = node.module
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            deco = None
            for d in node.decorator_list:
                if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute):
                    attr = d.func.attr
                    if attr in ("get", "post", "put", "patch", "delete"):
                        deco = (attr.upper(), d)
                        break
            if deco is None:
                continue
            method, d = deco
            path = None
            if d.args:
                a0 = d.args[0]
                if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                    path = a0.value
            if path is None:
                continue
            full = prefix + path if path.startswith("/") else prefix + "/" + path
            target = delegated_call_name(node, set(imported.keys()))
            if target is None:
                continue
            mod = imported[target]
            mapping.setdefault(mod, []).append((fn, method, full, target))
    return mapping


def analyze_controllers():
    results = {}
    for dirpath, _, files in os.walk(CONTROLLERS_DIR):
        for fn in sorted(files):
            if not fn.endswith(".py") or fn == "__init__.py":
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace(os.sep, ".")
            mod = rel[:-3]
            try:
                text = open(full, encoding="utf-8").read()
                tree = ast.parse(text)
            except Exception:
                results[mod] = {"error": "parse"}
                continue
            defines_router = "APIRouter(" in text and (
                "router = APIRouter" in text or "router=APIRouter" in text)
            has_self_router_deco = False
            has_ar_deco = False
            funcs = []
            has_commit = False
            defined_funcs = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    defined_funcs.add(node.name)
                    for d in node.decorator_list:
                        if isinstance(d, ast.Call):
                            f = d.func
                            if isinstance(f, ast.Name) and f.id in ("get", "post", "put", "patch", "delete", "route"):
                                has_ar_deco = True
                            if isinstance(f, ast.Attribute) and f.attr in ("get", "post", "put", "patch", "delete", "websocket"):
                                has_self_router_deco = True
                    # scan body for commit/flush
                    for sub in ast.walk(node):
                        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                            nm = sub.func.attr
                            if nm in ("commit", "flush") and isinstance(sub.func.value, ast.Name) and sub.func.value.id in ("db", "session"):
                                has_commit = True
                        if isinstance(sub, ast.Attribute) and sub.attr in ("commit", "flush") and isinstance(sub.value, ast.Name) and sub.value.id in ("db", "session"):
                            has_commit = True
                    funcs.append(node.name)
            results[mod] = {
                "file": rel,
                "defines_router": defines_router,
                "has_self_router_deco": has_self_router_deco,
                "has_ar_deco": has_ar_deco,
                "funcs": funcs,
                "defined_funcs": defined_funcs,
                "has_commit": has_commit,
            }
    return results


def main():
    mapping = analyze_routers()
    controllers = analyze_controllers()

    # Only count a router->controller reference if the delegated function is
    # actually DEFINED in the controller module (re-export shims don't count).
    for mod, refs in list(mapping.items()):
        defined = controllers.get(mod, {}).get("defined_funcs", set())
        mapping[mod] = [r for r in refs if r[3] in defined]

    print("=" * 100)
    print("CONTROLLER ELIGIBILITY ANALYSIS")
    print("=" * 100)
    rows = []
    for mod, info in sorted(controllers.items()):
        if "error" in info:
            continue
        if info["has_ar_deco"]:
            status = "ALREADY MIGRATED"
            reasons = []
        else:
            refs = mapping.get(mod, [])
            routers = sorted(set(r[0] for r in refs))
            surfaces = sorted(set(surface_for(r[2])[0] for r in refs if surface_for(r[2])))
            reasons = []
            if info["defines_router"] or info["has_self_router_deco"]:
                reasons.append("C4:self-defined router")
            if len(routers) == 0:
                reasons.append("C2:not referenced by any router")
            elif len(routers) > 1:
                reasons.append(f"C2:referenced by {len(routers)} routers: {routers}")
            if len(surfaces) > 1:
                reasons.append(f"C1:multi-surface {surfaces}")
            elif len(surfaces) == 0:
                reasons.append("C1:no surface")
            if info["has_commit"]:
                reasons.append("C3:commit/flush in body")
            status = "ELIGIBLE" if not reasons else "NO"
        rows.append((mod, status, reasons, mapping.get(mod, [])))

    for mod, status, reasons, refs in rows:
        if status == "ALREADY MIGRATED":
            print(f"[MIGRATED] {mod}")
        elif status == "ELIGIBLE":
            print(f"[ELIGIBLE] {mod}  (router(s): {sorted(set(r[0] for r in refs))})")
            for r in refs:
                print(f"            {r[1]:7} {r[2]:45} -> {r[3]}")
        else:
            print(f"[   NO   ] {mod}  :: {reasons}")
    print("=" * 100)
    elig = [mod for mod, s, _, _ in rows if s == "ELIGIBLE"]
    print(f"ELIGIBLE count: {len(elig)} -> {elig}")


if __name__ == "__main__":
    main()
