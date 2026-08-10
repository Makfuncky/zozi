"""Scan for invalid `__table_args__` patterns across models/.

Detects:
  A) Tuple with a dict not in last position
  B) BinOp concat chain where a `({"schema": ...},)` tuple is not the LAST
     operand (the schema kwarg tuple must be final for SQLAlchemy)
"""
import ast
import glob


def tuple_has_mid_dict(els):
    return [
        i for i, el in enumerate(els)
        if isinstance(el, ast.Dict) and i != len(els) - 1
    ]


def concat_chain_mid_schema(value):
    """Walk a BinOp (+ chain); return list of operand positions with schema tuples not last."""
    ops = []
    cur = value
    while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Add):
        ops.append(cur.left)
        cur = cur.right
    ops.append(cur)
    bad = []
    for i, op in enumerate(ops):
        if isinstance(op, ast.Tuple):
            els = op.elts
            if any(isinstance(el, ast.Dict) for el in els):
                if i != len(ops) - 1:
                    bad.append(i)
        elif isinstance(op, ast.Call) and isinstance(op.func, ast.Name) and op.func.id == "_get_table_args":
            pass
        else:
            # arbitrary operand; only flag schema dicts inside nested tuples elsewhere
            for n in ast.walk(op):
                if isinstance(n, ast.Dict) and any(
                    isinstance(k, ast.Constant) and k.value == "schema" for k in n.keys
                ):
                    bad.append(i)
                    break
    return bad


issues = []
for path in sorted(glob.glob("backend/models/**/*.py", recursive=True)):
    if "__pycache__" in path:
        continue
    src = open(path, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        issues.append((path, f"SYNTAX line {e.lineno}"))
        continue
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
                if isinstance(v, ast.Tuple):
                    if tuple_has_mid_dict(v.elts):
                        issues.append((path, f"MID-TUPLE {node.name}"))
                elif isinstance(v, ast.BinOp):
                    bad = concat_chain_mid_schema(v)
                    if bad:
                        issues.append((path, f"CONCAT-MID-SCHEMA {node.name} positions {bad}"))

print(f"issues: {len(issues)}")
for p, why in issues:
    print(f"  {p}: {why}")
