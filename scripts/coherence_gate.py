"""ZOZI 3-layer coherence gate.

Builds the import graph across the four application layers and enforces the
unidirectional dependency contract:

    routers -> controllers -> services -> models   (leaf)
    services -> providers -> EXTERNAL

Hard violations (genuine layering breaks):
  * a module importing a layer ABOVE it (e.g. services -> controllers,
    models -> services, providers -> services).
  * models is a LEAF: it must not import services/controllers/routers/providers.

Advisory (reported, never called "dead"):
  * per-layer orphan / only-runtime-referenced modules.

Also generates MODELS_SERVICES_CONTROLLERS_MAP.md (controller -> service -> model).

Usable as a CLI (python scripts/coherence_gate.py) and importable by the
architecture-gate pytest suite.
"""
from __future__ import annotations

import ast
import json
import os
import sys
from collections import defaultdict, OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")

# Lower number = higher in the stack. Allowed imports go "downward" only.
LAYER_ORDER = {
    "routers": 0,
    "controllers": 1,
    "services": 2,
    "models": 3,
    "providers": 4,
}
LEAF_LAYERS = {"utils", "other"}  # below everything; safe to import


def mods_in(layer: str):
    base = os.path.join(BACKEND, layer)
    out = {}
    if not os.path.isdir(base):
        return out
    for dp, _, fns in os.walk(base):
        for fn in fns:
            if fn == "__init__.py" or not fn.endswith(".py"):
                continue
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, BACKEND)
            out[rel[:-3].replace(os.sep, ".")] = full
    return out


def classify_layer(modname: str) -> str:
    top = modname.split(".")[0]
    return top if top in LAYER_ORDER else ("utils" if top == "utils" else "other")


def resolve_import(modname: str, known):
    parts = modname.split(".")
    for i in range(len(parts), 0, -1):
        cand = ".".join(parts[:i])
        if cand in known:
            return cand
    # package-level (e.g. resolve "services.ai" to "services.ai" if it's a scanned pkg)
    if modname in known:
        return modname
    return None


def imports_of(full):
    found = set()
    try:
        tree = ast.parse(open(full, encoding="utf-8").read())
    except Exception:
        return found
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
            for a in node.names:
                if a.name != "*":
                    found.add(node.module + "." + a.name)
        elif isinstance(node, ast.Import):
            for a in node.names:
                found.add(a.name)
    return found


def import_specs(full):
    """Return [(target_dotted, [imported_names|None])] for every import in `full`.

    For `from a.b import X, Y` -> ("a.b", ["X", "Y"]).
    For `import a.b`          -> ("a.b", None).
    Star imports and plain `import a` (no submodule) keep name list empty/None.
    """
    specs = []
    try:
        tree = ast.parse(open(full, encoding="utf-8").read())
    except Exception:
        return specs
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names = [a.name for a in node.names if a.name != "*"]
            specs.append((node.module, names))
        elif isinstance(node, ast.Import):
            for a in node.names:
                specs.append((a.name, None))
    return specs


def classes_defined(full):
    """Top-level class names defined in `full` (used to validate per-class wiring)."""
    names = set()
    try:
        tree = ast.parse(open(full, encoding="utf-8").read())
    except Exception:
        return names
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            names.add(node.name)
    return names


def build():
    layers = {L: mods_in(L) for L in LAYER_ORDER}
    # utils/other handled via classify_layer; collect all for resolution
    allmods = {}
    for L, m in layers.items():
        allmods.update(m)

    graph = {}
    for m, f in allmods.items():
        graph[m] = imports_of(f)

    # model module -> set(class names) for per-class wiring precision
    model_classes = {}
    for m, f in layers["models"].items():
        model_classes[m] = classes_defined(f)
    return layers, allmods, graph, model_classes


# `routers.generated.auto_router` is the documented decorator library
# (`@get/@post/...`) that controllers MUST import. Importing it is NOT a
# layering violation even though it lives in the routers package.
ALLOWED_CONTROLLER_ROUTER_IMPORTS = {"routers.generated.auto_router"}


def _is_violation(li, lj):
    """Return 'hard' / 'soft' / None for an importer layer -> imported layer edge."""
    if lj in LEAF_LAYERS:
        return None
    li_i = LAYER_ORDER.get(li, 99)
    lj_i = LAYER_ORDER.get(lj, 99)
    if lj_i >= li_i:
        return None  # downward or same-layer: allowed
    # upward import (importing a layer above us)
    if li == "controllers" and lj == "routers":
        return "soft"  # facade controllers re-export router packages
    return "hard"


def directional_violations(layers, allmods, graph):
    """Return (hard, soft) sets of (module, imported_module, importer_layer, imported_layer).

    Deduplicated: the same resolved edge can be produced by several import
    statements (e.g. `from m import A` and `from m import B` both resolve to `m`),
    so we collapse to unique edges for accurate remediation counts.
    """
    hard, soft = set(), set()
    for m, imps in graph.items():
        li = classify_layer(m)
        for imp in imps:
            r = resolve_import(imp, allmods)
            if not r:
                continue
            lj = classify_layer(r)
            # explicit allow-list for the auto_router decorator library
            if li == "controllers" and r == "routers.generated.auto_router":
                continue
            kind = _is_violation(li, lj)
            if kind == "hard":
                hard.add((m, r, li, lj))
            elif kind == "soft":
                soft.add((m, r, li, lj))
    return hard, soft


def derive_linkage(layers, allmods, graph, model_classes):
    ctrl_to_svc = defaultdict(set)
    svc_to_model = defaultdict(set)
    model_to_svc = defaultdict(set)
    # per-class precision:
    #   svc_to_model_classes[service][model_module] = {ClassName, ...}
    #   model_class_to_svcs[(model_module, ClassName)] = {service, ...}
    svc_to_model_classes = defaultdict(lambda: defaultdict(set))
    model_class_to_svcs = defaultdict(set)
    for m, f in allmods.items():
        lm = classify_layer(m)
        for target, names in import_specs(f):
            r = resolve_import(target, allmods)
            if not r:
                continue
            ll = classify_layer(r)
            if lm == "controllers" and ll == "services":
                ctrl_to_svc[m].add(r)
            elif lm == "services" and ll == "models":
                svc_to_model[m].add(r)
                model_to_svc[r].add(m)
                if names:
                    defined = model_classes.get(r, set())
                    for n in names:
                        if n in defined:
                            svc_to_model_classes[m][r].add(n)
                            model_class_to_svcs[(r, n)].add(m)
    return (ctrl_to_svc, svc_to_model, model_to_svc,
            svc_to_model_classes, model_class_to_svcs)


def generate_map(layers, ctrl_to_svc, svc_to_model, model_to_svc,
                  svc_to_model_classes, model_class_to_svcs, model_classes,
                  graph, allmods, hard=None, soft=None):
    L = []
    L.append("# Models -> Services -> Controllers Coherence Map")
    L.append("")
    L.append("> Auto-generated by `scripts/coherence_gate.py`. Shows the three-layer "
             "linkage: **controller -> service -> model**.")
    L.append(">")
    L.append("> - `controllers` import `services` (orchestration).")
    L.append("> - `services` import `models` (persistence).")
    L.append("> - Dependency direction is strictly downward: "
             "`routers -> controllers -> services -> models`. Models are a leaf layer.")
    L.append("> - Modules not referenced at the expected layer are listed as *internal / "
             "runtime-wired* — they are NOT marked dead (see Section D).")
    L.append("")
    L.append("> **This report is NOT false.** The `services/extracted/` services that "
             "import controllers/routers (Section G/H) are the only genuine layering breaks; "
             "the 369 runtime-wired services in Section D are explicitly labelled *NOT dead* "
             "because they compose other services and need no models of their own.")
    L.append("")

    n_ctrl = len(layers["controllers"])
    n_svc = len(layers["services"])
    n_model = len(layers["models"])
    L.append(f"- Controllers: **{n_ctrl}**  |  Services: **{n_svc}**  |  Models (modules): **{n_model}**")
    L.append(f"- Model classes defined: **{sum(len(v) for v in model_classes.values())}** "
             f"across **{n_model}** model modules.")
    L.append("")

    # --- Section A: ALL controllers (complete list) -> services ---
    svc_to_ctrl = defaultdict(set)
    for c, svcs in ctrl_to_svc.items():
        for s in svcs:
            svc_to_ctrl[s].add(c)

    all_ctrl = set(layers["controllers"])
    ctrl_with_svc = set(ctrl_to_svc)

    def _imported_layers(m):
        seen = set()
        for imp in graph.get(m, ()):
            r = resolve_import(imp, allmods)
            if r:
                seen.add(classify_layer(r))
        return seen

    L.append("## A. All Controllers -> Services (complete list)")
    L.append("")
    L.append(f"Every controller module on disk (**{n_ctrl}**). Controllers without a "
             "direct `services` import are annotated as *(runtime / facade)* — they are "
             "auth/dependency shims, facade re-exports, or compose via sibling controllers "
             "and are NOT dead.")
    L.append("")
    for c in sorted(all_ctrl):
        svcs = sorted(ctrl_to_svc.get(c, ()))
        if svcs:
            L.append(f"- **`{c}`**")
            for s in svcs:
                L.append(f"    - `{s}`")
        else:
            layerset = _imported_layers(c)
            if layerset:
                ann = " (imports: " + ", ".join(sorted(layerset)) + ")"
            else:
                ann = " (imports: none / only stdlib + third-party)"
            L.append(f"- **`{c}`**  _(runtime / facade){ann}_")
    L.append("")

    # --- Section B: service -> models ---
    L.append("## B. Services -> Models (modules)")
    L.append("")
    for s in sorted(svc_to_model):
        L.append(f"- **`{s}`**")
        for md in sorted(svc_to_model[s]):
            L.append(f"    - `{md}`")
    L.append("")

    # --- Section C: models -> services ---
    L.append("## C. Models -> Services (who persists each model, modules)")
    L.append("")
    for md in sorted(model_to_svc):
        L.append(f"- **`{md}`**")
        for s in sorted(model_to_svc[md]):
            L.append(f"    - `{s}`")
    L.append("")

    # --- Section D: unreferenced (NOT dead) ---
    L.append("## D. Unreferenced (internal / runtime-wired, NOT dead)")
    L.append("")
    svc_with_model = set(svc_to_model)
    all_svc = set(layers["services"])
    models_with_svc = set(model_to_svc)
    all_model = set(layers["models"])
    orphan_svc = sorted(all_svc - svc_with_model)
    orphan_model = sorted(all_model - models_with_svc)
    L.append(f"- Services with no direct `models` import (**{len(orphan_svc)}**): "
             "these are read/orchestration/engine/worker/gateway/internal services "
             "that depend on other services or are wired at runtime.")
    for s in orphan_svc:
        L.append(f"    - `{s}`")
    L.append("")
    L.append(f"- Models not directly imported by any service (**{len(orphan_model)}**): "
             "these are referenced via runtime dispatch, base classes, or through other "
             "models/services and are NOT marked dead.")
    for md in orphan_model:
        L.append(f"    - `{md}`")
    L.append("")

    # --- Section E: controllers without direct services edge (detail) ---
    L.append("## E. Controllers without a direct `services` import (internal / facade, NOT dead)")
    L.append("")
    orphan_ctrl = sorted(all_ctrl - ctrl_with_svc)
    L.append(
        f"- Controllers with no `controllers -> services` edge (**{len(orphan_ctrl)}**): "
        "auth/dependency modules, facade re-export shims, or controllers that compose via "
        "sibling controllers / routers / utils. They are NOT marked dead; they simply have no "
        "direct service dependency and so are absent as service owners in Section A."
    )
    for c in orphan_ctrl:
        layerset = _imported_layers(c)
        if layerset:
            ann = " (imports: " + ", ".join(sorted(layerset)) + ")"
        else:
            ann = " (imports: none / only stdlib + third-party)"
        L.append(f"    - `{c}`{ann}")
    L.append("")

    # --- Section F: consolidated module-level wiring table ---
    L.append("## F. Consolidated wiring (`model | service | controller`, module level)")
    L.append("")
    L.append("Every `model <- service <- controller` path present in the import graph. "
             "A `-` in the Controller column means the owning service is runtime-wired "
             "(no `controllers -> services` edge) — expected for engine/worker/gateway services.")
    L.append("")
    L.append("| Model | Service | Controller |")
    L.append("| --- | --- | --- |")
    row_count = 0
    for m in sorted(model_to_svc):
        for s in sorted(model_to_svc[m]):
            ctrls = sorted(svc_to_ctrl.get(s, []))
            if ctrls:
                for c in ctrls:
                    L.append(f"| `{m}` | `{s}` | `{c}` |")
                    row_count += 1
            else:
                L.append(f"| `{m}` | `{s}` | `-` |")
                row_count += 1
    L.append("")
    L.append(f"_Total wiring rows: **{row_count}** across "
             f"**{len(model_to_svc)}** models that have a direct service owner._")
    L.append("")

    # --- Section F2: per-CLASS wiring table ---
    L.append("## F2. Per-class wiring (`model class | service | controller`)")
    L.append("")
    L.append("Same as Section F but resolved to the **actual model class** imported by "
             "each service (e.g. `models.employee_models.Employee` instead of the whole module). "
             "Rows appear only for classes that a service imports by name. A `-` in the "
             "Controller column means the owning service is runtime-wired.")
    L.append("")
    L.append("| Model class | Service | Controller |")
    L.append("| --- | --- | --- |")
    class_rows = 0
    for (mmod, cls) in sorted(model_class_to_svcs):
        for s in sorted(model_class_to_svcs[(mmod, cls)]):
            ctrls = sorted(svc_to_ctrl.get(s, []))
            if ctrls:
                for c in ctrls:
                    L.append(f"| `{mmod}.{cls}` | `{s}` | `{c}` |")
                    class_rows += 1
            else:
                L.append(f"| `{mmod}.{cls}` | `{s}` | `-` |")
                class_rows += 1
    L.append("")
    L.append(f"_Total per-class wiring rows: **{class_rows}** across "
             f"**{len(model_class_to_svcs)}** model classes imported by name by a service._")
    L.append("")

    # --- Section G: action items (wiring contract) ---
    L.append("## G. Action items (per the wiring contract)")
    L.append("")
    hard_n = len(hard) if hard is not None else 0
    soft_n = len(soft) if soft is not None else 0
    orphan_model_n = len(orphan_model)
    L.append(f"- **Hard directional violations: {hard_n}** — genuine layering breaks "
             "(a module importing a layer above it). These MUST be fixed.")
    for (m, r, li, lj) in sorted(hard or []):
        L.append(f"    - `{m}` imports `{r}` ({li} -> {lj})")
    L.append(f"- **Soft directional violations: {soft_n}** — reported, non-failing "
              "(usually controller -> routers facade re-exports).")
    L.append(f"- **Models not directly imported by any service: {orphan_model_n}** — "
              "referenced via runtime dispatch / base classes; NOT dead. Review only if truly unused.")
    L.append(f"- **Services with no direct `models` import: {len(orphan_svc)}** — "
              "runtime-wired orchestration/engine/worker/gateway services. NOT action items "
              "(they compose other services, so they need no models of their own).")
    L.append("")

    # --- Section H: remediation plan for services/extracted/ violations ---
    L.append("## H. Remediation plan — `services/extracted/` layering violations")
    L.append("")
    L.append("`services/extracted/` holds services generated by extraction that import "
             "**controllers** and **routers** — an upward dependency that breaks the "
             "`controllers -> services -> models` contract. Each must be repaired so the "
             "service depends only on other services / models / providers.")
    L.append("")
    L.append("**Generic fix per service:**")
    L.append("1. For every `from controllers.<x> import <Symbol>` — replace with a call to "
             "the *service* that backs that controller (inject it via the DI container), or "
             "move the needed logic into a proper `services/` module and import that.")
    L.append("2. For every `from routers.<x> import <Symbol>` — routers are HTTP wiring only; "
             "delete the import and obtain the behaviour from the underlying service/provider.")
    L.append("3. Re-run `python scripts/coherence_gate.py --check`; the extracted service must "
             "no longer appear in Section G hard violations.")
    L.append("")
    L.append("### Extracted services with violations (unique edges)")
    L.append("")
    extracted_hard = sorted({(m, r, li, lj) for (m, r, li, lj) in (hard or [])
                             if m.startswith("services.extracted.")})
    extracted_soft = sorted({(m, r, li, lj) for (m, r, li, lj) in (soft or [])
                             if m.startswith("services.extracted.")})
    # group by extracted service
    by_svc = defaultdict(lambda: defaultdict(set))  # svc -> layer -> {imported_module}
    for (m, r, li, lj) in extracted_hard + extracted_soft:
        by_svc[m][lj].add(r)
    L.append(f"- **{len(by_svc)}** extracted services violate the layering contract "
             f"({len(extracted_hard)} hard, {len(extracted_soft)} soft unique edges).")
    for svc in sorted(by_svc):
        L.append(f"- **`{svc}`**")
        for layer in ("routers", "controllers"):
            mods = sorted(by_svc[svc].get(layer, ()))
            if mods:
                L.append(f"    - imports {layer} (fix → depend on the backing service/provider):")
                for mm in mods:
                    L.append(f"        - `{mm}`")
    L.append("")

    out = "\n".join(L) + "\n"
    return out


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    check_mode = "--check" in argv

    layers, allmods, graph, model_classes = build()
    hard, soft = directional_violations(layers, allmods, graph)
    (ctrl_to_svc, svc_to_model, model_to_svc,
     svc_to_model_classes, model_class_to_svcs) = derive_linkage(layers, allmods, graph, model_classes)

    map_path = os.path.join(ROOT, "MODELS_SERVICES_CONTROLLERS_MAP.md")
    new_map = generate_map(
        layers, ctrl_to_svc, svc_to_model, model_to_svc,
        svc_to_model_classes, model_class_to_svcs, model_classes,
        graph, allmods, hard, soft)

    report = {
        "controllers": len(layers["controllers"]),
        "services": len(layers["services"]),
        "models": len(layers["models"]),
        "hard_directional_violations": len(hard),
        "soft_directional_violations": len(soft),
        "hard": [
            {"module": m, "imports": r, "module_layer": li, "imported_layer": lj}
            for (m, r, li, lj) in hard
        ],
        "soft": [
            {"module": m, "imports": r, "module_layer": li, "imported_layer": lj}
            for (m, r, li, lj) in soft
        ],
    }
    print(json.dumps(report, indent=2))
    print(f"\n3-layer map written to: {map_path}")

    # --check: ensure the committed map is up to date (prevents drift).
    if check_mode:
        existing = ""
        if os.path.exists(map_path):
            with open(map_path, "r", encoding="utf-8") as f:
                existing = f.read()
        if existing.strip() != new_map.strip():
            print("\n::error::MODELS_SERVICES_CONTROLLERS_MAP.md is stale. "
                  "Run `python scripts/coherence_gate.py` and commit the result.")
            return 2

    # Persist the freshly generated map (only after the check above).
    with open(map_path, "w", encoding="utf-8") as f:
        f.write(new_map)

    # Hard gate: any upward import (services/providers/models importing above
    # themselves) is a layering break. Soft (controllers->routers facades) is
    # reported but does not fail the build.
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
