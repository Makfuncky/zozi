import pathlib, ast, re

root = pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\models")
# files and lines flagged by DBA01
targets = {
    "admin.py": [46, 113],
    "core.py": [159],
    "permissions.py": [19, 36, 53, 67, 80],
    "user.py": [19, 79, 93, 139, 153, 167],
}

changed = 0
for rel, lines in targets.items():
    f = root / rel
    text = f.read_text(encoding="utf-8")
    out_lines = text.splitlines()
    for ln in lines:
        idx = ln - 1
        line = out_lines[idx]
        # case A: element preceded by a comma -> remove ", {"schema": "core"}"
        if ", {" in line and '{"schema": "core"}' in line:
            out_lines[idx] = line.replace(', {"schema": "core"}', "")
        # case B: only element -> remove '{"schema": "core"},' (leaves empty tuple)
        elif '{"schema": "core"},' in line:
            out_lines[idx] = line.replace('{"schema": "core"},', "")
        else:
            print(f"UNHANDLED: {rel}:{ln} -> {line.strip()}")
            continue
        changed += 1
    new_text = "\n".join(out_lines)
    # sanity: still parses
    ast.parse(new_text)
    f.write_text(new_text, encoding="utf-8")

print(f"Removed {changed} schema='core' declarations; all files parse OK.")

# verify none remain
pat = re.compile(r"""schema["']?\s*[:=]\s*['"]core['"]""")
remain = 0
for f in root.rglob("*.py"):
    for i, ln in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if pat.search(ln):
            print("REMAINS:", f, i, ln.strip())
            remain += 1
print("remaining core schema declarations in models:", remain)
