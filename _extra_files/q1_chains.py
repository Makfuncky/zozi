"""Q1 chain-shape analyzer (temp, read-only).

For every ``db.query(...)`` site, walk UP the AST to the outermost chained call
and record the ordered chain of methods (filter/join/order_by/.../terminal).
This tells us exactly which db_read helpers are needed.
"""
from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BACKEND = REPO / "backend"
LAYERS = ("routers", "controllers", "middleware", "dependencies")
SESSION_NAMES = {"db", "session", "sess", "s", "db_session"}


def session_vars(tree):
    names = set(SESSION_NAMES)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for a in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                if a.arg in SESSION_NAMES:
                    names.add(a.arg)
                elif a.annotation is not None and (
                    "Session" in ast.dump(a.annotation)
                ):
                    names.add(a.arg)
    return names


def build_parents(tree):
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def chain_of(call, parents):
    """Return (chain_methods, outermost_node) walking up from db.query(...)."""
    chain = []
    node = call
    while True:
        p = parents.get(node)
        # node -> Attribute(node.method) -> Call
        if isinstance(p, ast.Attribute) and p.value is node:
            gp = parents.get(p)
            if isinstance(gp, ast.Call) and gp.func is p:
                chain.append(p.attr)
                node = gp
                continue
            chain.append(p.attr + "<prop>")
            node = p
            continue
        break
    return chain, node


def main():
    rows = []
    for layer in LAYERS:
        d = BACKEND / layer
        if not d.exists():
            continue
        for py in sorted(d.rglob("*.py")):
            if "__pycache__" in py.parts:
                continue
            try:
                text = py.read_text(encoding="utf-8")
                tree = ast.parse(text)
            except Exception:
                continue
            lines = text.splitlines()
            svars = session_vars(tree)
            parents = build_parents(tree)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                obj = node.func.value
                obj_name = obj.id if isinstance(obj, ast.Name) else (
                    obj.attr if isinstance(obj, ast.Attribute) else None
                )
                if obj_name not in svars:
                    continue
                verb = node.func.attr
                if verb not in {"query", "execute", "get", "scalar", "scalars",
                                "first", "all", "one", "one_or_none"}:
                    continue
                chain, outer = chain_of(node, parents)
                start = node.lineno
                end = getattr(outer, "end_lineno", start) or start
                rows.append({
                    "file": str(py.relative_to(REPO)),
                    "line": start,
                    "verb": verb,
                    "chain": chain,
                    "nargs": len(node.args),
                    "src": "\n".join(lines[start - 1:end]).strip(),
                })

    (REPO / "_extra_files" / "q1_chains.json").write_text(
        json.dumps(rows, indent=1), encoding="utf-8")

    shapes = Counter(" -> ".join(r["chain"]) or "(bare)" for r in rows)
    methods = Counter(m for r in rows for m in r["chain"])
    terminals = Counter((r["chain"][-1] if r["chain"] else "(bare)") for r in rows)

    print(f"TOTAL sites: {len(rows)}\n")
    print("-- terminal op --")
    for k, v in terminals.most_common():
        print(f"  {k:<22} {v}")
    print("\n-- every chain method used --")
    for k, v in methods.most_common():
        print(f"  {k:<22} {v}")
    print("\n-- top 40 distinct chain shapes --")
    for k, v in shapes.most_common(40):
        print(f"  {v:>4}  {k}")
    print(f"\ndistinct shapes: {len(shapes)}")


if __name__ == "__main__":
    main()
