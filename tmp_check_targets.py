import re, glob, os

versions_dir = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\alembic\versions"
files = sorted(glob.glob(os.path.join(versions_dir, '*.py')))
files = [f for f in files if os.path.basename(f) not in ('__init__.py',)]

targets = {
    'internal_messages': ['is_deleted', 'path', 'depth', 'ix_org_unit', 'sales_order_lines_id', 'sales_order_lines_so_id'],
    'org_units': ['is_deleted', 'path', 'depth', 'ix_org_unit'],
    'sales_order_lines': ['path', 'depth', 'ix_sales_order_lines_id', 'ix_sales_order_lines_so_id'],
}

for fn in files:
    content = open(fn, encoding='utf-8').read()
    rev = re.search(r"revision:\s*['\"]([^'\"]+)['\"]", content)
    rev = rev.group(1) if rev else '?'
    for t in targets:
        if t in content:
            ops = [x for x in targets[t] if x in content]
            print(f"{fn:70} rev={rev:22} -> {t}: {', '.join(ops)}")
