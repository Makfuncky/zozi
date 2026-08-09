import re, ast
from pathlib import Path
BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
tokens = ["_get_category_recommendations","_UNSET","_before_send","_first_currency",
          "_log_comm_event","_extract_terms","_fallback","_apply_stripe_runtime_key",
          "_get_product_cache_version","_build_ai_input","_merge_ai_output","_default_country",
          "_extract_product_name","_extract_variant_from_text","_compact_evidence"]
for n in tokens:
    rx = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(n) + r"(?![A-Za-z0-9_])")
    cnt = 0; files = set()
    for f in BACKEND.rglob("*.py"):
        try:
            t = f.read_text(encoding="utf-8")
        except Exception:
            continue
        m = rx.findall(t)
        if m:
            cnt += len(m); files.add(f.relative_to(BACKEND).as_posix())
    print(f"{n:<32} private={cnt} files={sorted(files)[:4]}")
