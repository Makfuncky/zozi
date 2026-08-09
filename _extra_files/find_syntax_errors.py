import ast, glob, os, sys

root = sys.argv[1] if len(sys.argv) > 1 else "."
bad = []
for f in glob.glob(os.path.join(root, "**", "*.py"), recursive=True):
    try:
        with open(f, encoding="utf-8") as fh:
            ast.parse(fh.read())
    except SyntaxError as e:
        bad.append((f, e.lineno, e.msg, (e.text or "").strip()[:80]))

for f, ln, msg, text in sorted(bad):
    print(f"{f}:{ln}: {msg} | {text}")
print("TOTAL_SYNTAX_ERRORS", len(bad))
