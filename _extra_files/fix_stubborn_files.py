"""Fix remaining CIR2 imports in two write-locked files in one pass."""
import importlib
import pathlib
import re
import sys
import time

BACKEND = pathlib.Path(__file__).resolve().parents[1] / "backend"
DATA = BACKEND / "data"

SHIM = '''"""Auto-generated forwarder shim for the exempt `data` facade."""
import importlib
import sys

_target = "{target}"
try:
    _m = sys.modules[_target]
except KeyError:
    _m = importlib.import_module(_target)

for _k in dir(_m):
    if not _k.startswith("__"):
        globals()[_k] = getattr(_m, _k)
'''


def _write(p, text):
    last = None
    for a in range(10):
        try:
            p.write_text(text, encoding="utf-8")
            return
        except OSError as e:
            last = e
            time.sleep(0.2 * (a + 1))
    raise last


def fix_file(fp):
    p = BACKEND.parent / fp
    text = p.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    changed = False
    pat = re.compile(r"^(?P<indent>\s*)from\s+(?P<mod>(?:models|services|providers)(?:\.\w+)*)\s+import\b")
    for i, line in enumerate(lines):
        m = pat.match(line)
        if not m:
            continue
        mod = m.group("mod")
        shim = mod.replace(".", "_")
        sp = DATA / f"{shim}.py"
        if not sp.exists():
            _write(sp, SHIM.format(target=mod))
        lines[i] = f"{m.group('indent')}from data.{shim} import" + line[m.end():]
        changed = True
    if changed:
        _write(p, "\n".join(lines) + ("\n" if text.endswith("\n") else ""))
        print(f"fixed {fp}")
    return changed


for fp in ["backend/routers/admin_treasury.py", "backend/routers/supplier.py"]:
    fix_file(fp)
