import os, re
ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
for name in ["logistics_partner.py", "customer_coupons.py", "auth.py", "supplier_orders.py"]:
    p = os.path.join(ROOT, "backend", "routers", name)
    src = open(p, encoding="utf-8", errors="ignore").read()
    routes = re.findall(r"@\w+\.(get|post|put|patch|delete)\(\s*['\"]([^'\"]*)['\"]", src)
    defs = re.findall(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", src)
    print(name, "src_len", len(src), "routes", len(routes), "defs", len(defs))
    print("   first defs:", defs[:5])
