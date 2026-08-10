"""Safe FK-hygiene transform for the ZOZI backend.

For every model column that is a ``Column`` containing a ``ForeignKey``:
  * ensure the ``ForeignKey`` has an explicit ``ondelete`` (add ``RESTRICT`` if
    missing — safe default; preserves existing CASCADE/SET NULL),
  * ensure the column is indexed (add ``index=True`` if missing and not already
    covered by an explicit ``__table_args__`` Index).

Each Column is rewritten exactly once via AST unparse (its nested ForeignKey is
modified in place), so there are no overlapping edits. Clears audit DBA07+DBA08.

Scope: all backend/*.py EXCEPT tests, scripts, migrations, alembic.
"""
from __future__ import annotations

import ast
from pathlib import Path

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
SKIP_DIRS = {
    "tests", "scripts", "migrations", "alembic", "venv", ".venv",
    "__pycache__", ".git", "node_modules",
}


def _is_func(func: ast.AST, name: str) -> bool:
    if isinstance(func, ast.Name):
        return func.id == name
    if isinstance(func, ast.Attribute):
        return func.attr == name
    return False


def _table_args_text(cls: ast.ClassDef) -> str:
    for stmt in cls.body:
        if isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if isinstance(t, ast.Name) and t.id == "__table_args__":
                    try:
                        return ast.unparse(stmt.value).lower()
                    except Exception:
                        return ""
    return ""


def _line_has_multi_assign(line_text: str) -> bool:
    depth = 0
    in_str = None
    assigns = 0
    i = 0
    while i < len(line_text):
        c = line_text[i]
        if in_str:
            if c == in_str and (i + 1 >= len(line_text) or line_text[i + 1] != in_str):
                in_str = None
            elif c == in_str:
                i += 2
                continue
            i += 1
            continue
        if c in "\"'":
            in_str = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth = max(0, depth - 1)
        elif c == "=" and depth == 0:
            if i + 1 >= len(line_text) or line_text[i + 1] not in "=<>!+/":
                assigns += 1
        i += 1
    return assigns > 1


class _SpanFinder(ast.NodeVisitor):
    def __init__(self, lines: list[str]):
        self.prefix = [0] * (len(lines) + 1)
        for i, ln in enumerate(lines):
            self.prefix[i + 1] = self.prefix[i] + len(ln)

    def _offset(self, lineno: int, col: int) -> int:
        return self.prefix[lineno - 1] + col

    def visit(self, node):
        if hasattr(node, "lineno") and hasattr(node, "col_offset") and hasattr(
            node, "end_lineno"
        ) and hasattr(node, "end_col_offset"):
            s = self._offset(node.lineno, node.col_offset)
            e = self._offset(node.end_lineno, node.end_col_offset)
            node._span = (s, e)  # type: ignore[attr-defined]
        self.generic_visit(node)


def _unparse_preserve(node: ast.AST) -> str:
    # ast.unparse uses single quotes; keep source's double-quote style.
    return ast.unparse(node).replace("'", '"')


def main() -> int:
    changed = fk_edits = idx_edits = skipped = 0
    for path in sorted(BACKEND.rglob("*.py")):
        rel = path.relative_to(BACKEND).parts[:-1]
        if set(rel) & SKIP_DIRS:
            continue
        if path.name.startswith("test_") or "system_trackers" in path.parts:
            continue
        try:
            src = path.read_text(encoding="utf-8")
            tree = ast.parse(src)
        except (OSError, SyntaxError):
            continue

        lines = src.splitlines(keepends=True)
        _SpanFinder(lines).visit(tree)

        # edits: (start, end, new_text)
        edits: list[tuple[int, int, str, int]] = []
        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef):
                continue
            tbl_args = _table_args_text(cls).lower()
            for stmt in cls.body:
                if not (isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call)):
                    continue
                col = stmt.value
                if not _is_func(col.func, "Column"):
                    continue
                fk_nodes = [
                    a for a in col.args
                    if isinstance(a, ast.Call) and _is_func(a.func, "ForeignKey")
                ]
                if not fk_nodes:
                    continue
                # multi-assignment line guard
                if _line_has_multi_assign(lines[stmt.lineno - 1]):
                    skipped += 1
                    continue
                col_name = (
                    stmt.targets[0].id
                    if isinstance(stmt.targets[0], ast.Name)
                    else None
                )
                need_index = not any(kw.arg == "index" for kw in col.keywords)
                if need_index and col_name and col_name.lower() in tbl_args:
                    need_index = False
                modified = False
                for fk in fk_nodes:
                    if not any(kw.arg == "ondelete" for kw in fk.keywords):
                        fk.keywords.append(
                            ast.keyword(arg="ondelete", value=ast.Constant("RESTRICT"))
                        )
                        fk_edits += 1
                        modified = True
                if need_index:
                    col.keywords.append(
                        ast.keyword(arg="index", value=ast.Constant(True))
                    )
                    idx_edits += 1
                    modified = True
                if modified:
                    sp = col._span  # type: ignore[attr-defined]
                    new_text = _unparse_preserve(col)
                    edits.append((sp[0], sp[1], new_text, stmt.lineno))

        if not edits:
            continue
        pieces: list[str] = []
        cursor = 0
        for start, end, new_text, _ln in sorted(edits, key=lambda e: e[0]):
            assert src[start:end] == src[start:end], "no-op"
            pieces.append(src[cursor:start])
            pieces.append(new_text)
            cursor = end
        pieces.append(src[cursor:])
        new_src = "".join(pieces)
        # safety: new source must still parse
        try:
            ast.parse(new_src)
        except SyntaxError:
            print(f"SKIP (would corrupt) {path}")
            continue
        path.write_text(new_src, encoding="utf-8")
        changed += 1

    print(f"changed files: {changed}")
    print(f"FK ondelete edits: {fk_edits}")
    print(f"FK index edits: {idx_edits}")
    print(f"skipped (shared-line) edits: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
