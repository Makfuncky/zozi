"""API101 fixer: add response_model to endpoints that lack one.

Strategy (output-preserving + safe):
  * Inject `response_model=dict` into the route decorator Call via exact
    AST source positions (no full reformatting, so existing style is kept).
  * Skip endpoints that legitimately have no body:
      - decorator has status_code=204
      - function only returns None / Response subclasses (no data path)
  * Skip test files (reported as false positives instead).

`dict` is used because it documents "returns JSON/dict" and does NOT filter
fields, so existing responses are unchanged.
"""
from __future__ import annotations
import ast
import os
import sys
from pathlib import Path

BACKEND = Path("backend")
SKIP = {"venv", "node_modules", "__pycache__", ".venv", ".git", "experiments"}
ROUTE_SUFFIXES = (".get", ".post", ".put", ".patch", ".delete")
RESPONSE_CLASSES = {
    "Response", "RedirectResponse", "JSONResponse", "FileResponse",
    "StreamingResponse", "HTMLResponse", "PlainTextResponse",
    "UJSONResponse", "ORJSONResponse",
}


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted(node.value) + "." + node.attr
    return ""


def is_test_file(path: Path) -> bool:
    parts = path.relative_to(BACKEND).parts
    return any(x in parts for x in {"tests", "test", "e2e", "testing",
                                    "loadtests", "validation"})


def is_route_dec(dec):
    dname = dotted(dec.func) if isinstance(dec, ast.Call) else dotted(dec)
    return any(s in dname for s in ROUTE_SUFFIXES)


def returns_only_no_body(tree, func):
    """True if every return yields None or a Response subclass (no data)."""
    saw_return = False
    for n in ast.walk(func):
        if isinstance(n, ast.Return):
            saw_return = True
            val = n.value
            if val is None:
                continue
            if isinstance(val, ast.Call):
                fn = dotted(val.func).split(".")[-1]
                if fn in RESPONSE_CLASSES:
                    continue
            # any other value => data path
            return False
    return saw_return


def process_file(path: Path):
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except Exception as e:
        print(f"  PARSE FAIL {path}: {e}")
        return 0
    lines = src.splitlines(keepends=True)

    edits = []  # (end_lineno, end_col_offset, text_to_insert_before_rparen)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        route_decs = [d for d in node.decorator_list if is_route_dec(d)]
        if not route_decs:
            continue
        # already has response_model somewhere?
        has_rm = any(
            isinstance(d, ast.Call) and any(k.arg == "response_model" for k in d.keywords)
            for d in route_decs
        )
        if has_rm:
            continue
        # pick the (first) route decorator Call
        dec = next(d for d in route_decs if isinstance(d, ast.Call))
        # skip legitimate no-body endpoints
        status204 = any(
            kw.arg == "status_code" and isinstance(kw.value, ast.Constant)
            and kw.value.value == 204
            for kw in dec.keywords
        )
        if status204:
            continue
        if returns_only_no_body(tree, node):
            continue
        # insert before the closing ')' of the Call
        edits.append((dec.end_lineno, dec.end_col_offset, ", response_model=dict"))

    if not edits:
        return 0
    # apply edits from bottom to top so offsets stay valid
    edits.sort(key=lambda e: (e[0], e[1]), reverse=True)
    new_lines = list(lines)
    for ln, col, text in edits:
        idx = ln - 1
        # ast end_col_offset is a UTF-8 BYTE offset; operate on bytes so
        # non-ASCII decorators (e.g. "360°") don't shift the insertion point.
        b = new_lines[idx].encode("utf-8")
        bpos = col - 1  # 0-based byte offset of the ')'
        nb = b[:bpos] + text.encode("utf-8") + b[bpos:]
        new_lines[idx] = nb.decode("utf-8")
    path.write_text("".join(new_lines), encoding="utf-8")
    return len(edits)


def main():
    apply = "--apply" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    files = []
    for root, dirs, fs in os.walk(BACKEND):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in fs:
            if f.endswith(".py"):
                p = Path(root) / f
                if only and not any(str(p).endswith(o) for o in only):
                    continue
                if is_test_file(p):
                    continue
                files.append(p)
    total = 0
    for p in files:
        n = process_file(p) if apply else 0
        if apply and n:
            print(f"  +{n}  {p.relative_to(BACKEND)}")
            total += n
    if apply:
        print(f"TOTAL endpoints fixed: {total}")
    else:
        print("DRY RUN (no changes). Pass --apply to write. "
              "Use a filename suffix arg to scope, e.g. admin_banners_governance.py")


if __name__ == "__main__":
    main()
