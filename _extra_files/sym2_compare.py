import sys, ast, pathlib, hashlib

def normalize(src):
    tree = ast.parse(src)
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue  # drop docstrings / string literals
    ast.fix_missing_locations(tree)
    try:
        return ast.unparse(tree)
    except Exception:
        return src

def body_hash(src):
    return hashlib.sha1(normalize(src).encode()).hexdigest()[:10]

def dump(path, name):
    src = pathlib.Path(path).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            seg = ast.get_source_segment(src, node)
            print(f"=== {path}:{node.lineno}  hash={body_hash(seg)} ===")
            print(seg)
            print()

if __name__ == "__main__":
    name = sys.argv[1]
    for f in sys.argv[2:]:
        dump(f, name)
