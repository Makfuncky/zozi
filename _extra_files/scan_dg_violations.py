"""Scan the backend for DG (forbidden dependency-graph edge) violations.

Faithfully replicates scripts/system_trackers/system_architecture_audit.py
check_dependency_graph() DG detection so we can enumerate the exact 191
violations (file, line, caller_layer -> target) before remediation.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
BACKEND = REPO / "backend"

DEFAULT_FORBIDDEN_EDGES = {
    "middleware": ["services", "controllers", "routers", "models", "providers", "events", "jobs"],
    "dependencies": ["services", "controllers", "routers", "models", "providers", "events", "jobs"],
    "routers": ["providers", "db.database", "db.create_tables", "db.init_db"],
    "controllers": ["routers", "middleware", "dependencies", "db.database", "db.create_tables", "db.init_db"],
    "services": ["routers", "controllers", "middleware", "dependencies"],
    "providers": ["routers", "controllers", "services", "models", "middleware", "dependencies",
                  "db.database", "db.create_tables", "db.init_db", "events", "jobs"],
    "models": ["routers", "controllers", "services", "providers", "middleware", "dependencies", "events", "jobs"],
    "events": ["routers", "controllers", "middleware", "dependencies"],
    "jobs": ["routers", "controllers", "middleware", "dependencies"],
    "utils": ["routers", "controllers", "services", "models", "providers", "middleware",
              "dependencies", "db.database", "db.create_tables", "db.init_db"],
    "db": ["routers", "controllers", "services", "providers", "middleware", "dependencies", "events", "jobs"],
}
EXPECTED_BACKEND_PACKAGES = ["routers", "controllers", "services", "models", "middleware",
                              "dependencies", "providers", "utils", "db", "alembic",
                              "tests", "scripts", "events", "jobs", "data"]
GRAPH_EXEMPT_LAYERS = {"tests", "scripts", "alembic", "monitoring", "docs", "data"}


def backend_module_name(pyfile: Path, backend_dir: Path):
    try:
        rel_path = pyfile.relative_to(backend_dir).with_suffix("")
    except ValueError:
        return None
    parts = list(rel_path.parts)
    if not parts:
        return None
    if parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts:
        return None
    return ".".join(parts)


def normalize_import(raw, known_top):
    if not raw:
        return None
    raw = raw.strip().strip(".")
    if not raw:
        return None
    if raw.startswith("backend."):
        raw = raw[len("backend."):]
    first = raw.split(".", 1)[0]
    if first in known_top:
        return raw
    return None


def resolve_relative_import(level, module, pkg):
    if level == 0:
        return module
    if level - 1 > len(pkg):
        return None
    base = pkg[: len(pkg) - (level - 1)]
    parts = base + ([module] if module else [])
    return ".".join(parts) if parts else None


def parse_safe(path):
    try:
        return ast.parse(Path(path).read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def main():
    modules = {}
    known_top = {x.lower() for x in EXPECTED_BACKEND_PACKAGES}
    for f in BACKEND.rglob("*.py"):
        if "__pycache__" in f.parts or f.name == "conftest.py":
            continue
        m = backend_module_name(f, BACKEND)
        if not m:
            continue
        modules[m] = f
        known_top.add(m.split(".", 1)[0])

    imports = {}
    for module, f in modules.items():
        tree = parse_safe(f)
        if tree is None:
            continue
        try:
            pkg = list(f.relative_to(BACKEND).parent.parts)
        except ValueError:
            pkg = []
        lst = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    norm = normalize_import(alias.name, known_top)
                    if norm:
                        lst.append((norm, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                raw = resolve_relative_import(node.level, node.module, pkg)
                norm = normalize_import(raw, known_top)
                if norm:
                    lst.append((norm, node.lineno))
            if isinstance(node, ast.Call):
                fname = None
                if isinstance(node.func, ast.Name):
                    fname = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    fname = node.func.attr
                if fname in {"import_module", "__import__"} and node.args and \
                        isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    norm = normalize_import(node.args[0].value, known_top)
                    if norm:
                        lst.append((norm, node.lineno))
        imports[module] = lst

    def layer_of(m):
        return m.split(".", 1)[0] if m else ""

    violations = []
    for caller in sorted(imports):
        cl = layer_of(caller)
        if cl in GRAPH_EXEMPT_LAYERS:
            continue
        cpath = modules[caller].relative_to(REPO)
        edges = DEFAULT_FORBIDDEN_EDGES.get(cl, [])
        seen = set()
        for mod, line in imports[caller]:
            for pref in edges:
                if mod == pref or mod.startswith(pref + "."):
                    key = (pref, mod)
                    if key not in seen:
                        seen.add(key)
                        violations.append((str(cpath), cl, mod, line, pref))
                    break

    # Group summary
    from collections import Counter
    cc = Counter((v[1], v[4]) for v in violations)
    print("=" * 80)
    print(f"TOTAL DG VIOLATIONS: {len(violations)}")
    print("=" * 80)
    print("\nBy (caller_layer -> forbidden_prefix):")
    for (cl, pref), n in sorted(cc.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {n:4d}  {cl} -> {pref}")

    print("\nBy target prefix (top level of imported module):")
    cc2 = Counter(v[2].split(".")[0] if v[2] not in ("db.database", "db.create_tables", "db.init_db") else v[2] for v in violations)
    for tgt, n in sorted(cc2.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {n:4d}  imports targeting {tgt}")

    print("\n" + "=" * 80)
    print("DETAIL (caller_path | layer | forbidden_target | line | prefix):")
    print("=" * 80)
    for cpath, cl, mod, line, pref in sorted(violations, key=lambda v: (v[1], v[4], v[0])):
        print(f"{cpath}  |  {cl} -> {mod}  |  L{line}  |  via {pref}")


if __name__ == "__main__":
    main()
