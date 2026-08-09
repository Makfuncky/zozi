import re
from pathlib import Path

TESTS = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\tests")

# Category B: stale _ROUTER_NAME -> correct current router stem
RNAME_FIX = {
    "addresses": "public_addresses_access",
    "admin_cash": "admin_cash_governance",
    "admin_chat": "admin_chat_governance",
    "admin_users": "admin_users_governance",
    "geo": "public_geo_access",
    "hr": "public_hr_access",
    "shipments": "public_shipments_access",
    "ws_chat": "public_ws_chat_access",
}

mod_re = re.compile(r'_MODULE\s*=\s*["\']([^"\']+)["\']')
rname_re = re.compile(r'_ROUTER_NAME\s*=\s*["\']([^"\']+)["\']')
rfile_re = re.compile(r'(_ROUTER_FILE\s*=\s*_BACKEND_ROOT\s*/\s*"routers"\s*/\s*)"([^"]+)"')

fixed = []
for f in sorted(TESTS.glob("*q1_rescue.py")):
    txt = f.read_text(encoding="utf-8")
    if "_ROUTER_FILE" not in txt and "_MODULE" not in txt:
        continue  # controller test, handled separately
    rname = rname_re.search(txt)
    mod = mod_re.search(txt)
    new = txt
    if rname and rname.group(1) in RNAME_FIX:
        target = RNAME_FIX[rname.group(1)]
        new = new.replace(f'_ROUTER_NAME = "{rname.group(1)}"', f'_ROUTER_NAME = "{target}"')
        fixed.append((f.name, f"_ROUTER_NAME {rname.group(1)}->{target}"))
    elif mod:
        stem = mod.group(1).split(".")[-1]
        m = rfile_re.search(new)
        if m:
            repl = m.group(1) + '"' + stem + '.py"'
            new = new[: m.start()] + repl + new[m.end():]
            fixed.append((f.name, f"_ROUTER_FILE -> {stem}.py"))
    if new != txt:
        f.write_text(new, encoding="utf-8")

for x in fixed:
    print("FIXED", x)
print("total fixed:", len(fixed))
