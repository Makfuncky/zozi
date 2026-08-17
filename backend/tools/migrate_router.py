"""Semi-automated router -> controllers/services migrator.

For a hand-written top-level ``routers/<name>.py`` that embeds business logic,
produce:
  - services/<domain>/<name>_service.py   (extracted handler logic, verbatim bodies)
  - controllers/<domain>/<name>_controller.py  (thin route-contract wrappers)

Unsupported routes (custom Depends like require_supplier, file uploads,
websockets) are skipped so the tool never produces a broken migration. The
caller is expected to: delete the original router, regenerate the auto-router,
run the tests, then regenerate the baseline.

Usage:
  python tools/migrate_router.py routers/<name>.py
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTERS = os.path.join(ROOT, "routers")
SERVICES = os.path.join(ROOT, "services")
CONTROLLERS = os.path.join(ROOT, "controllers")

SURFACES = {
    "/api/v1/admin": "admin",
    "/api/v1/customer": "customer",
    "/api/v1/supplier": "supplier",
    "/api/v1/logistics": "logistics",
    "/api/v1/system": "system",
    "/api/v1/internal": "internal",
    "/api/v1": "public",
}
TRUE_BUILTINS = {
    "int", "str", "bool", "float", "bytes", "complex", "object", "type",
    "dict", "list", "set", "tuple", "frozenset", "None", "True", "False",
    "Exception", "BaseException",
}
FASTAPI_TYPES = {"Request", "BackgroundTasks", "Response", "StreamingResponse",
                 "UploadFile", "File", "HTTPException", "Query", "Body", "Depends"}
TYPING_TYPES = {"Optional", "List", "Dict", "Any", "Union", "Tuple", "Set",
                 "Sequence", "Mapping", "Literal", "Callable", "Type"}
# SQLAlchemy session/ORM types that legitimately appear in a controller's
# dependency-injected ``db`` parameter; import them from sqlalchemy.orm,
# never from the service module.
SQLA_TYPES = {"Session", "AsyncSession", "Select", "Query"}


def _classify_type(name):
    if name in TRUE_BUILTINS:
        return "builtin"
    if name in FASTAPI_TYPES:
        return "fastapi"
    if name in TYPING_TYPES:
        return "typing"
    if name in SQLA_TYPES:
        return "sqlalchemy"
    return "service"


def _bucket(name, svc_types, fastapi_types, typing_types, sqlalchemy_types=None):
    kind = _classify_type(name)
    if kind == "builtin":
        return
    if kind == "fastapi":
        fastapi_types.add(name)
    elif kind == "typing":
        typing_types.add(name)
    elif kind == "sqlalchemy":
        if sqlalchemy_types is not None:
            sqlalchemy_types.add(name)
    else:
        svc_types.add(name)
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def up(node):
    return ast.unparse(node)


def unparse_arg(a):
    if a.annotation is not None:
        return f"{a.arg}: {up(a.annotation)}"
    return a.arg


def render_params(node):
    parts = []
    for a in getattr(node.args, "posonlyargs", []):
        parts.append(unparse_arg(a))
    for a in node.args.args:
        parts.append(unparse_arg(a))
    if node.args.vararg:
        parts.append("*" + node.args.vararg.arg)
    for a in node.args.kwonlyargs:
        parts.append(unparse_arg(a))
    if node.args.kwarg:
        parts.append("**" + node.args.kwarg.arg)
    return ", ".join(parts)


def surface_for_path(path):
    best = None
    for pref, name in SURFACES.items():
        if path.startswith(pref) and (best is None or len(pref) > len(best[0])):
            best = (pref, name)
    return best[1] if best else "core"


def collect_type_names(text):
    return {t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text)}


# Auth / role dependencies that map onto the controller contract's KNOWN_DEPS.
# Anything not listed here is treated as a genuinely custom dependency and the
# route is skipped (so the migrator never produces a broken migration).
_ROLE_DEP_ALIASES = {
    "get_db": "db",
    "require_admin": "admin",
    "get_current_admin": "admin",
    "require_admin_2fa_verified": "admin",
    "require_super_admin": "admin",
    "get_current_user": "user",
    "get_current_user_optional": "optional_user",
    "require_logistics": "logistics",
    "require_supplier": "supplier",
    # Promoted / shared dependency factories (see infrastructure.utils.dependencies and
    # services/security/fraud_engine.py). These are genuine, expressible
    # controller dependencies, so the migrator can move the route.
    "require_treasury_access": "treasury",
    "require_coupon_admin": "coupon_admin",
    "_require_admin": "coupon_admin",
    "bearer_scheme": "bearer",
    "get_fraud_engine": "fraud_engine",
    "get_threat_updater": "threat_updater",
}


def classify_dep(default_src):
    """Return dep name for a FastAPI Depends/Query/Body default, or None."""
    if default_src is None:
        return None
    s = default_src.strip()
    if s.startswith("Depends("):
        inner = s[len("Depends("):-1].strip()
        if inner in _ROLE_DEP_ALIASES:
            return _ROLE_DEP_ALIASES[inner]
        return "CUSTOM"
    if s.startswith("Query("):
        return "QUERY"
    if s.startswith("Body("):
        return "BODY"
    return None


def find_prefix(source, tree):
    # Match ``prefix=`` anywhere inside the APIRouter(...) call — not only when it
    # is the first positional kwarg. Routers commonly declare
    # ``APIRouter(tags=[...], prefix="/api/v1/...")``; a regex anchored to the
    # opening paren would miss those and silently emit routes at the wrong (root)
    # path, which both breaks routing and creates duplicate-route collisions.
    m = re.search(r'APIRouter\([^)]*?prefix\s*=\s*["\']([^"\']*)["\']', source)
    if m:
        return m.group(1)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "__router_prefix__":
                    if isinstance(node.value, ast.Constant):
                        return node.value.value
    return ""


def is_route_decorator(dec):
    return (
        isinstance(dec, ast.Call)
        and isinstance(dec.func, ast.Attribute)
        and dec.func.attr in HTTP_METHODS
        and isinstance(dec.func.value, ast.Name)
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("router")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                   help="overwrite existing service/controller files (e.g. to "
                        "re-finish a router whose service was already committed)")
    args = ap.parse_args()

    rpath = args.router
    stem = os.path.splitext(os.path.basename(rpath))[0]
    source = open(rpath, encoding="utf-8").read()
    tree = ast.parse(source)
    lines = source.splitlines()

    prefix = find_prefix(source, tree)

    # Collect route handlers and helper/import/class statements in order.
    route_handlers = []  # list of dicts
    body_items = []      # ("import"|"class"|"helper"|"assign_const"|"skip", text)
    skipped = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.module == "fastapi":
                # Services own logic, not routers: drop the APIRouter import.
                kept = [a.name for a in node.names if a.name != "APIRouter"]
                if kept:
                    body_items.append(("import", "from fastapi import " + ", ".join(kept)))
            else:
                body_items.append(("import", "\n".join(lines[node.lineno-1:node.end_lineno])))
        elif isinstance(node, ast.ClassDef):
            body_items.append(("class", "\n".join(lines[node.lineno-1:node.end_lineno])))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            deco = next((d for d in node.decorator_list if is_route_decorator(d)), None)
            if deco is None:
                body_items.append(("helper", "\n".join(lines[node.lineno-1:node.end_lineno])))
                continue
            # Parse route decorator
            method = deco.func.attr
            deco_path = deco.args[0].value if deco.args else None
            if deco_path is None:
                print(f"  SKIP {stem}: route without path", file=sys.stderr)
                body_items.append(("skip", ""))
                skipped += 1
                continue
            if deco_path == "":
                # Root route of the router (e.g. @router.get("")). Its full path
                # is exactly the router prefix.
                full = prefix
            else:
                full = deco_path if deco_path.startswith("/") else "/" + deco_path
                full = (prefix + full) if not full.startswith(prefix) else full
                if prefix and deco_path.startswith(prefix):
                    full = prefix + deco_path
            kwargs = {kw.arg: kw.value for kw in deco.keywords if kw.arg}
            # deps + unsupported detection from params
            deps = []
            unsupported = False
            ann_tokens = set()
            pos_args = node.args.args
            pos_defaults = node.args.defaults
            n_def = len(pos_defaults)
            all_args = list(getattr(node.args, "posonlyargs", [])) + list(pos_args)
            for a in all_args:
                if a.annotation is not None:
                    ann_tokens |= collect_type_names(up(a.annotation))
            for a in node.args.kwonlyargs:
                if a.annotation is not None:
                    ann_tokens |= collect_type_names(up(a.annotation))
            for i, a in enumerate(pos_args):
                dflt = pos_defaults[i - (len(pos_args) - n_def)] if i >= (len(pos_args) - n_def) else None
                dep = None
                if dflt is not None:
                    dep = classify_dep(up(dflt))
                else:
                    # no default: check annotation
                    if a.annotation is not None:
                        ann = up(a.annotation)
                        if ann == "Request":
                            dep = "request"
                        elif ann == "BackgroundTasks":
                            dep = "background_tasks"
                        elif ann in ("Session", "AsyncSession"):
                            # SQLAlchemy session injected without an explicit
                            # ``Depends(get_db)`` default — still a db dependency.
                            dep = "db"
                if dep == "CUSTOM":
                    unsupported = True
                elif dep == "QUERY":
                    pass  # handled by generator
                elif dep == "BODY":
                    pass
                elif dep in ("db", "admin", "user", "optional_user", "request", "background_tasks"):
                    if dep not in deps:
                        deps.append(dep)
                # annotation-based request/background already covered
            if unsupported:
                print(f"  SKIP route {stem}.{node.name}: custom dependency", file=sys.stderr)
                body_items.append(("skip", ""))
                skipped += 1
                continue
            # response_model + tags
            rm = kwargs.get("response_model")
            rm_text = up(rm) if rm is not None else None
            tags = kwargs.get("tags")
            tags_text = up(tags) if tags is not None else None
            sc = kwargs.get("status_code")
            sc_text = up(sc) if sc is not None else None
            # body range
            first_body = node.body[0].lineno
            body_src = "\n".join(lines[first_body-1:node.end_lineno])
            params_src = render_params(node)
            ret_src = (" -> " + up(node.returns)) if node.returns else ""
            is_async = isinstance(node, ast.AsyncFunctionDef)
            route_handlers.append({
                "name": node.name, "method": method, "full": full,
                "deps": deps, "rm": rm_text, "tags": tags_text, "sc": sc_text,
                "params": params_src, "body": body_src, "async": is_async,
                "lineno": node.lineno, "end": node.end_lineno,
                "returns": up(node.returns) if node.returns else None,
                "ann_types": ann_tokens,
                "param_names": [a.arg for a in getattr(node.args, "posonlyargs", []) or []]
                                + [a.arg for a in node.args.args]
                                + ([node.args.vararg.arg] if node.args.vararg else [])
                                + [a.arg for a in node.args.kwonlyargs]
                                + ([node.args.kwarg.arg] if node.args.kwarg else []),
            })
            # emit converted function later via body_items marker
            body_items.append(("route", route_handlers[-1]))
        elif isinstance(node, ast.Assign):
            tgts = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if tgts and tgts[0] in ("router", "__router_prefix__"):
                body_items.append(("skip", ""))
            else:
                body_items.append(("assign_const", "\n".join(lines[node.lineno-1:node.end_lineno])))
        else:
            body_items.append(("skip", ""))

    if not route_handlers:
        print(f"NO MIGRATABLE ROUTES in {stem}", file=sys.stderr)
        return 1

    # Domain + output paths
    domain = surface_for_path(route_handlers[0]["full"])
    svc_path = os.path.join(SERVICES, domain, f"{stem}_service.py")
    ctrl_path = os.path.join(CONTROLLERS, domain, f"{stem}_controller.py")

    # ---- Build service module text ----
    svc_lines = ['"""Auto-migrated service logic from routers/%s.py."""' % stem,
                 "from __future__ import annotations", ""]
    for kind, txt in body_items:
        if kind in ("import", "class", "helper", "assign_const"):
            svc_lines.append(txt)
            svc_lines.append("")
    for rh in route_handlers:
        header = ("async def " if rh["async"] else "def ") + rh["name"] + "(" + rh["params"] + ")" + ((" -> " + rh["returns"]) if rh["returns"] else "") + ":"
        svc_lines.append(header)
        svc_lines.append(rh["body"])
        svc_lines.append("")
    svc_text = "\n".join(svc_lines).rstrip() + "\n"

    # ---- Build controller module text ----
    methods = sorted({rh["method"] for rh in route_handlers})
    svc_types = set()       # annotation/return/response_model types from the service module
    fastapi_types = set()
    typing_types = set()
    sqlalchemy_types = set()
    for rh in route_handlers:
        if rh["rm"]:
            for t in collect_type_names(rh["rm"]):
                _bucket(t, svc_types, fastapi_types, typing_types, sqlalchemy_types)
        for t in rh.get("ann_types", set()):
            _bucket(t, svc_types, fastapi_types, typing_types, sqlalchemy_types)
        if rh["returns"]:
            for t in collect_type_names(rh["returns"]):
                _bucket(t, svc_types, fastapi_types, typing_types, sqlalchemy_types)

    ctrl_lines = ['"""Auto-migrated controller for routers/%s.py (thin route contract)."""' % stem,
                  "from __future__ import annotations", "",
                  "from modules.routers.generated.auto_router import " + ", ".join(methods), ""]
    if fastapi_types:
        ctrl_lines.append("from fastapi import " + ", ".join(sorted(fastapi_types)))
        ctrl_lines.append("")
    if typing_types:
        ctrl_lines.append("from typing import " + ", ".join(sorted(typing_types)))
        ctrl_lines.append("")
    if sqlalchemy_types:
        ctrl_lines.append("from sqlalchemy.orm import " + ", ".join(sorted(sqlalchemy_types)))
        ctrl_lines.append("")
    svc_mod = f"services.{domain}.{stem}_service"
    # import handler aliases + needed annotation types from service
    svc_imports = [f"{rh['name']} as _svc_{rh['name']}" for rh in route_handlers]
    if svc_types:
        svc_imports.extend(sorted(svc_types))
    ctrl_lines.append(f"from {svc_mod} import " + ", ".join(svc_imports))
    ctrl_lines.append("")
    for rh in route_handlers:
        deco_parts = [f'"{rh["full"]}"']
        if rh["deps"]:
            deco_parts.append("deps=[" + ", ".join('"%s"' % d for d in rh["deps"]) + "]")
        if rh["rm"]:
            deco_parts.append(f"response_model={rh['rm']}")
        if rh["tags"]:
            deco_parts.append(f"tags={rh['tags']}")
        if rh["sc"]:
            deco_parts.append(f"status_code={rh['sc']}")
        ctrl_lines.append(f"@{rh['method']}({', '.join(deco_parts)})")
        header = ("async def " if rh["async"] else "def ") + rh["name"] + "(" + rh["params"] + ")" + ((" -> " + rh["returns"]) if rh["returns"] else "") + ":"
        ctrl_lines.append(header)
        # build kwargs call from the real parameter names (do NOT re-parse the
        # rendered signature — annotations like ``Dict[str, Any]`` contain ", "
        # and would be torn apart by a naive split).
        call_parts = [f"{pname}={pname}" for pname in rh["param_names"]]
        ctrl_lines.append(f"    return _svc_{rh['name']}({', '.join(call_parts)})")
        ctrl_lines.append("")
    ctrl_text = "\n".join(ctrl_lines).rstrip() + "\n"

    # Validate generated sources parse before writing anything.
    for label, src in (("service", svc_text), ("controller", ctrl_text)):
        try:
            ast.parse(src)
        except SyntaxError as e:
            try:
                open(r"C:\Users\user\AppData\Local\Temp\kilo\debug_%s.txt" % label, "w", encoding="utf-8").write(src)
            except Exception:
                pass
            print(f"  ERROR: generated {label} for {stem} failed to parse: {e}", file=sys.stderr)
            return 1

    if args.dry_run:
        print(f"=== SERVICE {svc_path} ===")
        print(svc_text)
        print(f"=== CONTROLLER {ctrl_path} ===")
        print(ctrl_text)
        print(f"MIGRATE_PREVIEW {stem}: migratable={len(route_handlers)} skipped={skipped}", file=sys.stderr)
        return 0

    if skipped:
        print(f"  ABORT {stem}: {skipped} route(s) skipped (custom dep / upload / websocket). "
              f"Deleting the original would drop those routes — migrate them manually.", file=sys.stderr)
        return 2

    os.makedirs(os.path.dirname(svc_path), exist_ok=True)
    os.makedirs(os.path.dirname(ctrl_path), exist_ok=True)
    # avoid overwrite existing (unless --force, used to re-finish a router whose
    # service was already committed in a prior session).
    if not args.force:
        if os.path.exists(svc_path):
            print(f"  EXISTING {svc_path} — abort", file=sys.stderr); return 1
        if os.path.exists(ctrl_path):
            print(f"  EXISTING {ctrl_path} — abort", file=sys.stderr); return 1
    open(svc_path, "w", encoding="utf-8").write(svc_text)
    open(ctrl_path, "w", encoding="utf-8").write(ctrl_text)
    print(f"WROTE {svc_path}")
    print(f"WROTE {ctrl_path}")
    print(f"MIGRATE_OK {stem}: routes={len(route_handlers)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())


