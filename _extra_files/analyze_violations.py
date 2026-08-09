"""Analyze CIR1/CIR2 violations to plan data-shim rewrites (read-only)."""
import ast, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tests"))
import test_circuit_contract as t

BACKEND = pathlib.Path(__file__).resolve().parents[1] / "backend"

def parse(entry):
    toks = entry.split()
    rel = toks[0]
    caller = toks[1]
    target = toks[3]
    target_mod = toks[4].strip("()")
    return rel, caller, target, target_mod

def ast_of(path):
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return None

c1, c2 = t._scan()
plan = {}  # target_mod -> set of (file, kind)
for entry in c1 + c2:
    rel, caller, target, target_mod = parse(entry)
    fpath = rel.split(":")[0]
    lineno = int(rel.split(":")[-1])
    path = BACKEND.parent / fpath
    kind = "?"
    tree = ast_of(path)
    if tree:
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == target_mod and node.lineno == lineno:
                kind = "from"
                break
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name == target_mod and node.lineno == lineno:
                        kind = "import"
                        break
    plan.setdefault(target_mod, set()).add((fpath, kind))

print("DISTINCT VIOLATING TARGET MODULES:", len(plan))
for mod in sorted(plan):
    kinds = {k for _, k in plan[mod]}
    print(f"  {mod}  kinds={kinds}")
