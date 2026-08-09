import re
from pathlib import Path

TESTS = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\tests")
ROUTERS = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\routers")

mod_re = re.compile(r'_MODULE\s*=\s*["\']([^"\']+)["\']')
rf_re = re.compile(r'_ROUTER_FILE\s*=\s*_BACKEND_ROOT\s*/\s*"routers"\s*/\s*f?"\{([^}]+)\}"\.py' )
rf_re2 = re.compile(r'_ROUTER_FILE\s*=\s*_BACKEND_ROOT\s*/\s*"routers"\s*/\s*"([^"]+)"\.py')

problems = []
ok = []
for f in sorted(TESTS.glob("*q1_rescue.py")):
    txt = f.read_text(encoding="utf-8")
    mm = mod_re.search(txt)
    if not mm:
        problems.append((f.name, "no _MODULE"))
        continue
    mod = mm.group(1)
    # find _ROUTER_FILE basename
    rm = rf_re2.search(txt) or rf_re.search(txt)
    rf_base = rm.group(1) if rm else "??"
    # module file
    mod_file = ROUTERS / f"{mod.split('.')[-1]}.py"
    mod_exists = mod_file.exists()
    # stated router file
    stated_file = ROUTERS / f"{rf_base}.py"
    stated_exists = stated_file.exists()
    if mod_exists and stated_exists and mod_file == stated_file:
        ok.append(f.name)
    else:
        problems.append((f.name, mod, str(mod_file.name), mod_exists, rf_base, stated_exists))

print("=== PROBLEMS ===")
for p in problems:
    print(p)
print(f"\nOK (already consistent): {len(ok)}")
print(f"PROBLEMS: {len(problems)}")
