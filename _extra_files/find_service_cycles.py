"""Find circular imports among backend service modules (and their deps)."""
import ast
import os
import sys
from collections import defaultdict

SCAN_ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "services")
BACKEND = os.path.dirname(SCAN_ROOT) if SCAN_ROOT.endswith(("backend", "services")) else SCAN_ROOT

mod_path = {}
mod_name = {}
EXCLUDE = {"venv", "__pycache__", ".pytest_cache", ".hypothesis", "node_modules", "uploads", "static", "alembic", "docs", "zozi_mcp", "monitoring", "provider_test", "tools", "scripts", "tests", ".kilo"}
for root, _dirs, files in os.walk(SCAN_ROOT):
    _dirs[:] = [d for d in _dirs if d not in EXCLUDE]
    if "__pycache__" in root:
        continue
    for f in files:
        if not f.endswith(".py"):
            continue
        full = os.path.join(root, f)
        rel = os.path.relpath(full, BACKEND).replace(os.sep, "/")[:-3]
        name = rel.replace("/", ".")
        mod_path[name] = full
        mod_name[full] = name

# all modules under scan root
targets = set(mod_path)

graph = defaultdict(set)
for name, full in mod_path.items():
    if name not in targets:
        continue
    try:
        tree = ast.parse(open(full, encoding="utf-8").read())
    except Exception as e:
        print("PARSE FAIL", name, e)
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            graph[name].add(node.module)
        elif isinstance(node, ast.Import):
            for a in node.names:
                graph[name].add(a.name)
    # relative imports within packages: from . import x / from .x import y
    try:
        tree = ast.parse(open(full, encoding="utf-8").read())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                base = name.rsplit(".", 1)[0] if node.level == 1 else ".".join(name.split(".")[:-node.level])
                if node.module:
                    graph[name].add(base + "." + node.module)
                else:
                    for a in node.names:
                        if a.name != "*":
                            graph[name].add(base + "." + a.name)
                        else:
                            graph[name].add(base)
    except Exception:
        pass

# normalize targets: 'models' -> 'backend.models' etc., keep only edges to scanned modules
PREFIX = "backend."
for n in list(graph):
    norm = set()
    for t in graph[n]:
        cand = t if t in mod_path else (PREFIX + t if (PREFIX + t) in mod_path else None)
        if cand and cand in targets:
            norm.add(cand)
    graph[n] = norm

# Tarjan SCC (linear) — cycles == SCCs with >1 node (or self-loop)
index = {}
lowlink = {}
onstack = set()
stack = []
_counter = [0]
sccs = []

def strongconnect(v):
    index[v] = lowlink[v] = _counter[0]
    _counter[0] += 1
    stack.append(v)
    onstack.add(v)
    for w in sorted(graph.get(v, ())):
        if w not in index:
            strongconnect(w)
            lowlink[v] = min(lowlink[v], lowlink[w])
        elif w in onstack:
            lowlink[v] = min(lowlink[v], index[w])
    if lowlink[v] == index[v]:
        comp = []
        while True:
            w = stack.pop()
            onstack.discard(w)
            comp.append(w)
            if w == v:
                break
        if len(comp) > 1:
            sccs.append(comp)

for v in sorted(targets):
    if v not in index:
        strongconnect(v)

print(f"modules: {len(targets)}  cyclic SCCs: {len(sccs)}")
for comp in sorted(sccs, key=len, reverse=True):
    print("CYCLE (", len(comp), "):", " -> ".join(sorted(comp)))
