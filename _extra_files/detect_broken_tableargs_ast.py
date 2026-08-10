import ast, glob

def last_element(expr):
    if isinstance(expr, ast.Tuple):
        return expr.elts[-1] if expr.elts else None
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
        return last_element(expr.right)
    return expr

def is_schema(node):
    if isinstance(node, ast.Dict):
        return True
    if isinstance(node, ast.Tuple) and len(node.elts) == 1 and isinstance(node, ast.Tuple) and isinstance(node.elts[0], ast.Dict):
        return True
    return False

broken = []
for f in sorted(glob.glob('models/**/*.py', recursive=True)):
    try:
        src = open(f, encoding='utf-8').read()
        tree = ast.parse(src)
    except Exception as e:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], 'id', None) == '__table_args__':
            last = last_element(node.value)
            if last is None or not is_schema(last):
                broken.append((f, node.lineno))

for f, line in broken:
    print(f"{f}:{line}")
print("TOTAL BROKEN:", len(broken))
