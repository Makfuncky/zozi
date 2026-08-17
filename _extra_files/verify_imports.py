import importlib, sys, traceback, os, glob

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
sys.path.insert(0, ROOT)

EXCLUDE = {"venv", "__pycache__", ".git", "node_modules"}

def iter_py():
    for dirpath, dirs, files in os.walk(ROOT):
        parts = set(os.path.relpath(dirpath, ROOT).split(os.sep))
        if parts & EXCLUDE:
            dirs[:] = []
            continue
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(dirpath, f)

failures = []
for path in sorted(iter_py()):
    rel = os.path.relpath(path, ROOT)
    mod = rel[:-3].replace(os.sep, ".")
    if mod.endswith(".__init__"):
        mod = mod[:-9]
    try:
        importlib.import_module(mod)
        #print("OK", mod)
    except Exception as e:
        failures.append((mod, repr(e)))

print("TOTAL MODULES SCANNED:", "n/a")
print("FAILURES:", len(failures))
print("=" * 80)
for mod, err in failures:
    print(mod)
    print("   ", err)
