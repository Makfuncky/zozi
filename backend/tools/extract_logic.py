"""Delegating extractor: move router handler BUSINESS LOGIC (bodies, helpers,
db writes) into services/<domain>/<name>_service.py, leaving a thin delegating
router (routes/deps/prefixes unchanged) that calls the service.

This is a safe, mechanical migration that satisfies the W1 layer guard (no
session writes remain in routers/) while keeping the app bootable. It does not
produce controllers; the router surface is preserved. Run per router:

    python tools/extract_logic.py routers/<name>.py
"""
from __future__ import annotations

import argparse
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTERS = os.path.join(ROOT, "routers")
SERVICES = os.path.join(ROOT, "services")

SURFACES = {
    "/api/v1/admin": "admin",
    "/api/v1/customer": "customer",
    "/api/v1/supplier": "supplier",
    "/api/v1/logistics": "logistics",
    "/api/v1/system": "system",
    "/api/v1/internal": "internal",
    "/api/v1": "public",
}


def surface_for_path(prefix):
    best = None
    for pref, name in SURFACES.items():
        if prefix.startswith(pref) and (best is None or len(pref) > len(best[0])):
            best = (pref, name)
    return best[1] if best else "core"


def unparse(node):
    return ast.unparse(node)


def _render_arg(a, default):
    s = a.arg
    if a.annotation is not None:
        s += ": " + unparse(a.annotation)
    if default is not None:
        s += " = " + unparse(default)
    return s


def render_params(node):
    args = node.args
    parts = []
    for a in getattr(args, "posonlyargs", []):
        parts.append(_render_arg(a, None))
    n_args = len(args.args)
    n_defaults = len(args.defaults)
    off = n_args - n_defaults
    for i, a in enumerate(args.args):
        default = args.defaults[i - off] if i >= off else None
        parts.append(_render_arg(a, default))
    if args.vararg:
        parts.append("*" + args.vararg.arg)
    for i, a in enumerate(args.kwonlyargs):
        parts.append(_render_arg(a, args.kw_defaults[i]))
    if args.kwarg:
        parts.append("**" + args.kwarg.arg)
    return ", ".join(parts)


HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def is_route_decorator(dec):
    return (
        isinstance(dec, ast.Call)
        and isinstance(dec.func, ast.Attribute)
        and dec.func.attr in HTTP_METHODS
        and isinstance(dec.func.value, ast.Name)
    )


def is_router_assign(node):
    return (
        isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id != "router" for t in node.targets)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "APIRouter"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("router")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    rpath = args.router
    stem = os.path.splitext(os.path.basename(rpath))[0]
    source = open(rpath, encoding="utf-8").read()
    tree = ast.parse(source)
    lines = source.splitlines()

    # Find prefix
    prefix = ""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "router":
                    # look for APIRouter(prefix=...)
                    if (isinstance(node.value, ast.Call)
                            and isinstance(node.value.func, ast.Name)
                            and node.value.func.id == "APIRouter"):
                        for kw in node.value.keywords:
                            if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                                prefix = kw.value.value

    domain = surface_for_path(prefix or "/api/v1")
    svc_path = os.path.join(SERVICES, domain, f"{stem}_service.py")
    svc_mod = f"services.{domain}.{stem}_service"

    route_names = []
    helper_names = []
    service_top = []      # text lines for service (imports + helpers + handlers)
    router_top = []       # text lines for router (imports + helpers kept)
    router_routes = []    # delegating handler text

    # Decide which top-level names are route handlers
    handler_nodes = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(is_route_decorator(d) for d in node.decorator_list):
                handler_nodes[node.name] = node

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            txt = "\n".join(lines[node.lineno - 1:node.end_lineno])
            if txt.strip().startswith("from __future__"):
                service_top.append(txt)
                continue
            service_top.append(txt)
            router_top.append(txt)
        elif isinstance(node, ast.Assign):
            tgts = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if tgts and tgts[0] in ("router",) or is_router_assign(node):
                # keep in router only
                router_top.append("\n".join(lines[node.lineno - 1:node.end_lineno]))
            else:
                service_top.append("\n".join(lines[node.lineno - 1:node.end_lineno]))
                helper_names.extend(tgts)
        elif isinstance(node, ast.ClassDef):
            service_top.append("\n".join(lines[node.lineno - 1:node.end_lineno]))
            helper_names.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            if name in handler_nodes:
                route_names.append(name)
                # service: full function
                header = ("async def " if isinstance(node, ast.AsyncFunctionDef) else "def ") + name + "(" + render_params(node) + ")" + ((" -> " + unparse(node.returns)) if node.returns else "") + ":"
                body = "\n".join(lines[node.body[0].lineno - 1:node.end_lineno])
                service_top.append(header)
                service_top.append(body)
                service_top.append("")
                # router: delegator
                params = [a.arg for a in getattr(node.args, "posonlyargs", []) or []]
                params += [a.arg for a in node.args.args]
                params += ([node.args.vararg.arg] if node.args.vararg else [])
                params += [a.arg for a in node.args.kwonlyargs]
                params += ([node.args.kwarg.arg] if node.args.kwarg else [])
                deco = "\n".join(lines[node.lineno - 1:node.decorator_list[0].lineno]) if node.decorator_list else ""
                # recreate decorator text precisely
                deco_lines = []
                for d in node.decorator_list:
                    deco_lines.append("\n".join(lines[d.lineno - 1:d.end_lineno]))
                rheader = ("async def " if isinstance(node, ast.AsyncFunctionDef) else "def ") + name + "(" + render_params(node) + ")" + ((" -> " + unparse(node.returns)) if node.returns else "") + ":"
                call_args = ", ".join(f"{p}={p}" for p in params)
                router_routes.append("\n".join(deco_lines))
                router_routes.append(rheader)
                router_routes.append(f"    return {stem}_svc.{name}({call_args})")
                router_routes.append("")
            else:
                # helper function: move to service, keep name available in router
                service_top.append("\n".join(lines[node.lineno - 1:node.end_lineno]))
                service_top.append("")
                helper_names.append(name)
        else:
            # other top-level (e.g. include_router calls as expressions)
            txt = "\n".join(lines[node.lineno - 1:node.end_lineno])
            if "include_router" in txt:
                router_top.append(txt)
            else:
                service_top.append(txt)

    # Build service text
    svc_lines = [f'"""Business logic extracted from routers/{stem}.py."""',
                 "from __future__ import annotations", ""]
    for txt in service_top:
        # strip APIRouter from fastapi imports in service
        if "from fastapi import" in txt and "APIRouter" in txt:
            # remove APIRouter token
            import ast as _ast
            try:
                tree_imp = _ast.parse(txt)
                for imp in tree_imp.body:
                    if isinstance(imp, _ast.ImportFrom) and imp.module == "fastapi":
                        kept = [a.name + ((" as " + a.asname) if a.asname else "")
                                for a in imp.names if a.name != "APIRouter"]
                        if kept:
                            txt = "from fastapi import " + ", ".join(kept)
                        else:
                            txt = ""
            except Exception:
                pass
        if not txt.strip():
            continue
        if txt.strip().startswith("from __future__"):
            continue
        svc_lines.append(txt)
        svc_lines.append("")
    svc_text = "\n".join(svc_lines).rstrip() + "\n"

    # Build router text: keep original imports + router var + delegators
    router_lines = [f'"""Delegating router for {stem} (logic in {svc_mod})."""',
                    "from __future__ import annotations", ""]
    # import service symbols
    imported = sorted(set(route_names) | set(helper_names))
    router_lines.append("")
    router_lines.append(f"import {svc_mod} as {stem}_svc")
    if imported:
        router_lines.append(f"from {svc_mod} import " + ", ".join(imported))
    router_lines.append("")
    # router var + helpers kept
    for txt in router_top:
        if txt.strip():
            router_lines.append(txt)
            router_lines.append("")
    # route delegators
    for txt in router_routes:
        router_lines.append(txt)
    router_text = "\n".join(router_lines).rstrip() + "\n"

    # Validate
    for label, src in (("service", svc_text), ("router", router_text)):
        try:
            ast.parse(src)
        except SyntaxError as e:
            print(f"  ERROR generated {label} for {stem}: {e}", file=sys.stderr)
            return 1

    if args.dry_run:
        print("=== SERVICE ===\n" + svc_text)
        print("=== ROUTER ===\n" + router_text)
        return 0

    if not args.force and os.path.exists(svc_path):
        print(f"  EXISTING {svc_path} — use --force", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(svc_path), exist_ok=True)
    open(svc_path, "w", encoding="utf-8").write(svc_text)
    open(rpath, "w", encoding="utf-8").write(router_text)
    print(f"WROTE {svc_path}")
    print(f"REWROTE {rpath} (delegating)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
