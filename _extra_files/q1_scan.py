"""Q1 scanner — mirrors the auditor's check_layer_writes() read detection.

Read-only analysis helper (temp). Lists every session read call site in
routers/controllers/middleware/dependencies with the full source expression,
so the rescue work can be batched by shape.
"""
from __future__ import annotations

import ast
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BACKEND = REPO / "backend"

READ_VERBS = {
    "query", "get", "scalar", "scalars", "first", "all",
    "one", "one_or_none",
}
SKIP_VERBS = {"refresh", "expire", "expunge"}
SESSION_NAMES = {"db", "session", "sess", "s", "db_session"}
LAYERS = ("routers", "controllers", "middleware", "dependencies")


def session_vars(tree: ast.AST) -> set[str]:
    names = set(SESSION_NAMES)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args.args + node.args.posonlyargs + node.args.kwonlyargs
            for a in args:
                if a.arg in SESSION_NAMES:
                    names.add(a.arg)
                elif a.annotation is not None:
                    dumped = ast.dump(a.annotation)
                    if "Session" in dumped or "AsyncSession" in dumped:
                        names.add(a.arg)
    return names


def scan_file(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    lines = text.splitlines()
    svars = session_vars(tree)
    out: list[dict] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        method = node.func.attr
        obj = node.func.value
        if isinstance(obj, ast.Name):
            obj_name = obj.id
        elif isinstance(obj, ast.Attribute):
            obj_name = obj.attr
        else:
            continue
        if obj_name not in svars:
            continue
        if method in SKIP_VERBS:
            continue
        if method not in READ_VERBS and method != "execute":
            continue
        start = node.lineno
        end = getattr(node, "end_lineno", start) or start
        # widen to the full statement (chained .filter().all() etc.)
        stmt_end = end
        depth_probe = "\n".join(lines[start - 1: min(len(lines), stmt_end + 6)])
        out.append(
            {
                "file": str(path.relative_to(REPO)),
                "line": start,
                "verb": method,
                "recv": obj_name,
                "src": "\n".join(lines[start - 1: end]).strip(),
                "ctx": depth_probe,
            }
        )
    return out


def main() -> int:
    hits: list[dict] = []
    for layer in LAYERS:
        d = BACKEND / layer
        if not d.exists():
            continue
        for py in sorted(d.rglob("*.py")):
            if "__pycache__" in py.parts:
                continue
            hits.extend(scan_file(py))

    per_file = Counter(h["file"] for h in hits)
    per_verb = Counter(h["verb"] for h in hits)

    out_dir = REPO / "_extra_files"
    (out_dir / "q1_hits.json").write_text(
        json.dumps(hits, indent=1), encoding="utf-8"
    )

    print(f"TOTAL Q1 read sites: {len(hits)}")
    print("\n-- by verb --")
    for v, c in per_verb.most_common():
        print(f"  {v:<14} {c}")
    print("\n-- by file --")
    for f, c in per_file.most_common():
        print(f"  {c:>4}  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
