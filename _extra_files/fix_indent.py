import pathlib

FILES = [
    "routers/admin_fallback.py",
    "routers/admin_logistics_fallback.py",
    "routers/country_communications.py",
    "routers/finance.py",
    "routers/supplier_supplier_upload.py",
    "routers/store_payments_routes.py",
]

for rel in FILES:
    p = pathlib.Path(rel)
    lines = p.read_text(encoding="utf-8").splitlines()
    # find first line with `router = APIRouter` (module-level import zone ends here)
    router_idx = None
    for i, ln in enumerate(lines):
        if "router = APIRouter" in ln:
            router_idx = i
            break
    if router_idx is None:
        print("SKIP (no router line):", rel)
        continue
    changed = 0
    for i in range(router_idx + 1, len(lines)):
        ln = lines[i]
        if ln.startswith("from controllers.router_bridges.") and not ln.startswith("    "):
            lines[i] = "    " + ln
            changed += 1
    p.write_text(encoding="utf-8", data="\n".join(lines) + "\n")
    print(f"FIXED {rel}: indented {changed} line(s) (after line {router_idx+1})")
