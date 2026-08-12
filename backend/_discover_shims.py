import importlib, glob, os, re, sys, traceback
from collections import Counter

sys.path.insert(0, os.getcwd())

# candidate source files keyed by basename without extension
candidates = {}
for path in glob.glob(os.path.join('**', '*.py'), recursive=True):
    base = os.path.splitext(os.path.basename(path))[0]
    candidates.setdefault(base, []).append(path.replace('\\', '/'))

def first_target(tb):
    for line in tb.splitlines():
        m = re.search(r"No module named '([^']+)'", line)
        if m:
            return ('NMN', m.group(1).split('.')[-1])
        m = re.search(r"cannot import name '([^']+)' from", line)
        if m:
            return ('CIN', m.group(1))
        m = re.search(r"cannot import name '([^']+)'", line)
        if m:
            return ('CIN2', m.group(1))
    return None

missing = {}
for f in sorted(glob.glob(os.path.join('routers', '*.py'))):
    mod = 'routers.' + os.path.splitext(os.path.basename(f))[0]
    try:
        importlib.import_module(mod)
    except Exception:
        tgt = first_target(traceback.format_exc())
        if tgt:
            missing.setdefault(tgt[1], []).append(mod)

print("TOTAL DISTINCT", len(missing))
for tgt, used in sorted(missing.items(), key=lambda kv: -len(kv[1])):
    cands = candidates.get(tgt, [])
    print("### %s  (used by %d routers)" % (tgt, len(used)))
    if cands:
        for c in cands:
            print("   CANDIDATE:", c)
    else:
        print("   <NO CANDIDATE - likely deleted>")
