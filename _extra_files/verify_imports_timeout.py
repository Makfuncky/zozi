import importlib, os, sys, threading, traceback

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
sys.path.insert(0, ROOT)
EXCLUDE = {"venv", "__pycache__", ".git", "node_modules"}

def iter_modules():
    for dirpath, dirs, files in os.walk(ROOT):
        relparts = set(os.path.relpath(dirpath, ROOT).split(os.sep))
        if relparts & EXCLUDE:
            dirs[:] = []
            continue
        for f in files:
            if not f.endswith(".py") or f == "__init__.py":
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, ROOT)[:-3].replace(os.sep, ".")
            yield rel

results = {}
def worker(mod, out):
    try:
        importlib.import_module(mod)
        out.append((mod, "OK", ""))
    except ImportError as e:
        out.append((mod, "IMPORTERROR", str(e)))
    except Exception as e:
        out.append((mod, type(e).__name__, str(e)[:200]))

ok = imp_err = other = 0
imp_list = []
for mod in sorted(iter_modules()):
    out = []
    t = threading.Thread(target=worker, args=(mod, out), daemon=True)
    t.start()
    t.join(3.0)
    if t.is_alive():
        results[mod] = ("TIMEOUT", "")
        continue
    if not out:
        results[mod] = ("UNKNOWN", "")
        continue
    m, status, msg = out[0]
    results[mod] = (status, msg)

for mod, (status, msg) in sorted(results.items()):
    if status == "OK":
        ok += 1
    elif status == "IMPORTERROR":
        imp_err += 1
        imp_list.append((mod, msg))
    elif status == "TIMEOUT":
        pass
    else:
        other += 1

print("OK:", ok, "IMPORTERROR:", imp_err, "OTHER_EXC:", other, "TIMEOUT:", sum(1 for v in results.values() if v[0]=="TIMEOUT"))
print("=" * 90)
for mod, msg in imp_list:
    print("IMPORTERROR", mod)
    print("   ", msg)
