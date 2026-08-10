"""Generate routers from ``@route``-decorated controllers.

Controlled, run-on-demand, idempotent. Reads controller modules, collects
functions carrying a ``RouteSpec`` (set by ``utils.route``), and emits one
``APIRouter`` per module. The emitted router delegates to the controller
function via ``add_api_route`` — the controller keeps the real handler body
and FastAPI parameter annotations, so generated files stay tiny and never
drift from the source of truth.

Safety properties:
- Only modules that contain decorated functions are emitted. Undecorated
  controllers (the existing 157) are skipped, so no hand-written router is
  ever clobbered.
- Auth/RLS are passed as dependency objects; the generator imports them by
  reference. Nothing is guessed.
- Output is deterministic (routes sorted, stable formatting), so re-running
  produces byte-identical files.
- Import failures are skipped with a warning, never fatal.

Usage:
    CONTROLLER_INCLUDE=_poc_sample_controller ROUTER_GEN_OUT=./_poc_out \
        python scripts/gen_routers.py
"""
from __future__ import annotations

import importlib
import inspect
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.route import RouteSpec  # noqa: E402

LOG = logging.getLogger("gen_routers")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTROLLERS_DIR = os.path.join(BACKEND, "controllers")
OUTPUT_DIR = os.environ.get("ROUTER_GEN_OUT", os.path.join(BACKEND, "routers", "_auto"))
INCLUDE = {m.strip() for m in os.environ.get("CONTROLLER_INCLUDE", "").split(",") if m.strip()}


def controller_modules():
    for name in sorted(os.listdir(CONTROLLERS_DIR)):
        if not name.endswith(".py") or name.startswith("__"):
            continue
        mod = name[:-3]
        if INCLUDE and mod not in INCLUDE:
            continue
        yield "controllers." + mod


def discover():
    found = {}
    for modname in controller_modules():
        try:
            mod = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001
            LOG.warning("skip %s: %s", modname, exc)
            continue
        routes = []
        for _, obj in inspect.getmembers(mod, inspect.isfunction):
            spec = getattr(obj, "__route__", None)
            if isinstance(spec, RouteSpec):
                routes.append((obj.__name__, obj, spec))
        if routes:
            found[modname] = routes
    return found


def _ref_name(obj):
    """Bare name used in generated code; the object is imported explicitly."""
    if obj is None:
        return "None"
    return getattr(obj, "__name__", "None")


def render(modname, routes):
    prefix = next((s.prefix for _, _, s in routes if s.prefix), None)
    same_mod_imports = {n for n, _, _ in routes}
    other_imports = set()
    for _, _, s in routes:
        for obj in (s.auth, s.rls, s.response_model):
            if obj is None or not hasattr(obj, "__module__") or not hasattr(obj, "__name__"):
                continue
            if obj.__module__ == modname:
                same_mod_imports.add(obj.__name__)
            else:
                other_imports.add((obj.__module__, obj.__name__))

    lines = [
        f'"""AUTO-GENERATED router for {modname}. Do not edit by hand."""',
        "from fastapi import APIRouter, Depends",
    ]
    if same_mod_imports:
        lines.append(f"from {modname} import {', '.join(sorted(same_mod_imports))}")
    for mod, name in sorted(other_imports):
        lines.append(f"from {mod} import {name}")
    lines.append("")
    lines.append(f"router = APIRouter(prefix={prefix!r})")
    lines.append("")
    for name, _, spec in sorted(routes, key=lambda r: (r[2].path, r[2].method)):
        deps = []
        if spec.auth:
            deps.append(f"Depends({_ref_name(spec.auth)})")
        if spec.rls:
            deps.append(f"Depends({_ref_name(spec.rls)})")
        dep_arg = "[" + ", ".join(deps) + "]" if deps else "None"
        rm = _ref_name(spec.response_model) if spec.response_model else "None"
        lines.append("router.add_api_route(")
        lines.append(f"    {spec.path!r},")
        lines.append(f"    {name},")
        lines.append(f"    methods=[{spec.method!r}],")
        lines.append(f"    response_model={rm},")
        lines.append(f"    status_code={spec.status_code},")
        lines.append(f"    dependencies={dep_arg},")
        lines.append(f"    tags={spec.tags!r},")
        lines.append(")")
        lines.append("")
    return "\n".join(lines)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    found = discover()
    if not found:
        LOG.info("no decorated controllers found; nothing to generate")
        return
    for modname, routes in sorted(found.items()):
        out_name = modname.split(".")[-1] + ".py"
        out_path = os.path.join(OUTPUT_DIR, out_name)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(render(modname, routes))
        LOG.info("generated %s (%d route(s))", out_path, len(routes))


if __name__ == "__main__":
    main()
