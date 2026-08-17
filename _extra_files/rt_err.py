import os, sys, traceback
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
os.environ["APP_ENV"] = "development"
os.environ["PROMETHEUS_MULTIPROC_DIR"] = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\prom_tmp"
out = []
for m in ["admin_logistics_operations","admin_security_detection","public_core_admin","public_security_detection"]:
    out.append("==== " + m + " ====")
    try:
        __import__("routers." + m)
        out.append("  OK")
    except Exception:
        tb = traceback.format_exc().splitlines()
        # last frames; find the actionable message
        for line in reversed(tb):
            if any(k in line for k in ("Error", "assert", "Cannot", "Invalid", "line ")):
                out.append("  " + line.strip())
                break
with open(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\rt_err.txt", "w") as f:
    f.write("\n".join(out))
