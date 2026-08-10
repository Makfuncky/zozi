"""Fix `__table_args__` tuples where a schema dict is not the last element.

The agent's codemod appended new Index objects AFTER the `{"schema": ...}`
dict, which SQLAlchemy rejects ("SchemaItem expected, got {...}"). The fix
moves the dict to the last tuple position, preserving all other elements and
their exact source text.

Mechanical + surgical: only the element ORDER inside the tuple changes.
The tuple's exact source range is spliced (prefix/suffix untouched); fixes
are applied LAST-to-FIRST so earlier offsets stay valid.
Usage: python fix_table_args.py [target.py ...]  (default: backend/models/*.py)
"""
import ast
import glob
import sys

TARGETS = sys.argv[1:] if len(sys.argv) > 1 else sorted(glob.glob("backend/models/*.py"))


def char_offset(src, lineno, col):
    """1-indexed line / 0-indexed col -> absolute char offset."""
    lines = src.splitlines(keepends=True)
    return sum(len(l) for l in lines[: lineno - 1]) + col


FIXED = []
SKIPPED = []
for path in TARGETS:
    src = open(path, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        SKIPPED.append((path, f"syntax error line {e.lineno}"))
        continue

    # collect fixes: (start_char, end_char, element_texts, new_order, col)
    fixes = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign):
                continue
            for t in stmt.targets:
                if not (isinstance(t, ast.Name) and t.id == "__table_args__"):
                    continue
                v = stmt.value
                if not isinstance(v, ast.Tuple):
                    continue
                els = v.elts
                bad = [i for i, el in enumerate(els) if isinstance(el, ast.Dict) and i != len(els) - 1]
                if not bad:
                    continue
                i = bad[0]
                texts = [ast.get_source_segment(src, el).replace("\r", "") for el in els]
                new_order = [j for j in range(len(els)) if j != i] + [i]
                start = char_offset(src, v.lineno, v.col_offset)
                end = char_offset(src, v.end_lineno, v.end_col_offset)
                fixes.append((start, end, texts, new_order, v.col_offset))

    for start, end, texts, order, col in sorted(fixes, key=lambda f: f[0], reverse=True):
        indent = " " * col
        elem_indent = indent + "    "
        out = ["("]
        for j in order:
            t = texts[j].replace("\n", "\n" + elem_indent)
            out.append(elem_indent + t + ",")
        out.append(indent + ")")
        src = src[:start] + "\n".join(out) + src[end:]

    if fixes:
        open(path, "w", encoding="utf-8", newline="").write(src)
        FIXED.append(path)

print(f"FIXED ({len(FIXED)}):")
for p in FIXED:
    print("  ", p)
print(f"SKIPPED ({len(SKIPPED)}):")
for p, why in SKIPPED:
    print("  ", p, "-", why)
