"""Fast backend-only DG2 (domain cycle) checker.

Mirrors the spirit of system_architecture_audit.py's domain-graph cycle
detection but scoped to backend/ for speed. Edges that pass through exempt
layers (data, tests, scripts, alembic, monitoring, docs) are circuit breakers
and do NOT create domain edges.
"""
from __future__ import annotations
import ast
import os
import sys
from pathlib import Path

BACKEND = Path("backend")
SKIP_DIRS = {"venv", "node_modules", "__pycache__", "tests", "scripts",
             "experiments", ".venv", ".git"}
EXEMPT = {"data", "tests", "scripts", "alembic", "monitoring", "docs", "venv",
          "node_modules", "__pycache__", "experiments", "frontend", ".venv"}


def module_name(path: Path) -> str:
    rel = path.relative_to(BACKEND).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def collect_modules():
    mods = {}
    for root, dirs, files in os.walk(BACKEND):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".py"):
                p = Path(root) / f
                mods[module_name(p)] = p
    return mods


def imports_of(path: Path):
    """Resolve to the FULL target module (mirrors the audit's graph.edges),
    not just the top package."""
    out = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                out.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.module is None:
                continue
            if node.module:
                # Resolve relative imports against the package
                if node.level:
                    out.append(node.module)  # best-effort; audit handles precisely
                else:
                    out.append(node.module)
    return out


def domain_of(mod: str) -> str:
    parts = mod.split(".")
    if len(parts) >= 2:
        return parts[1]
    return parts[0]


def main():
    mods = collect_modules()
    # Domain graph: edge domain X -> domain Y if any module in X imports any
    # module in Y. Edges touching exempt first-segment layers are circuit
    # breakers and skipped (mirrors graph_exempt_layers).
    dom_adj = {}
    for m, p in mods.items():
        sd = domain_of(m)
        for tgt in imports_of(p):
            tgt_layer = tgt.split(".")[0]
            if tgt_layer in EXEMPT:
                continue
            if tgt in mods:
                td = domain_of(tgt)
                if td != sd:
                    dom_adj.setdefault(sd, set()).add(td)

    index = {}
    low = {}
    onstack = {}
    stack = []
    result = []
    counter = [0]

    def strongconnect(v):
        index[v] = counter[0]
        low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        onstack[v] = True
        for w in dom_adj.get(v, ()):
            if w not in index:
                strongconnect(w)
                low[v] = min(low[v], low[w])
            elif onstack.get(w):
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                onstack[w] = False
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                result.append(sorted(comp))

    for v in list(dom_adj):
        if v not in index:
            strongconnect(v)

    result.sort(key=lambda c: (len(c), c[0]))
    print(f"Modules scanned: {len(mods)}")
    print(f"Domain-level cycles (SCC size>1): {len(result)}")
    for comp in result:
        print("  CYCLE:", " -> ".join(comp))

    red_present = any("comms" in c and "employee_models" in c and
                      "employee_communication_service" in c for c in result)
    print("Previously-RED comms->employee_communication_service->employee_models->comms cycle present:",
          red_present)


if __name__ == "__main__":
    sys.exit(main())
