import ast, pathlib

f = pathlib.Path("backend/controllers/supplier/supplier_controller.py")
text = f.read_text(encoding="utf-8")
lines = text.splitlines(keepends=True)

tree = ast.parse(text)
# top-level function defs only
top_funcs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

def span(name):
    for n in top_funcs:
        if n.name == name:
            return n.lineno, n.end_lineno  # 1-based inclusive
    raise SystemExit(f"func not found: {name}")

# Range 1: from _round_badge_amount to run_badge_recalculation_cycle
s1 = span("_round_badge_amount")[0]
e1 = span("run_badge_recalculation_cycle")[1]
# Range 2: admin_set_supplier_badge
s2, e2 = span("admin_set_supplier_badge")

print("deleting ranges:", (s1, e1), (s2, e2))

# delete from the later range first to preserve earlier line numbers
def remove_range(lines, start, end):
    # start/end 1-based inclusive
    del lines[start - 1:end]  # slice end is exclusive -> end (inclusive) maps to end

remove_range(lines, s2, e2)
remove_range(lines, s1, e1)

# inject delegation import before the normalize_country_code import line
inject = (
    "from services.supplier.supplier_badge_service import (\n"
    "    admin_set_supplier_badge,\n"
    "    compute_credibility_score,\n"
    "    list_supplier_badge_billing_history,\n"
    "    list_supplier_badge_catalog,\n"
    "    purchase_supplier_badge,\n"
    "    record_badge_billing_payment,\n"
    "    refresh_supplier_badge,\n"
    "    run_badge_recalculation_cycle,\n"
    ")\n"
)
anchor = "from data.services_logistics_partner_pricing import normalize_country_code\n"
for i, ln in enumerate(lines):
    if ln == anchor:
        lines.insert(i, inject)
        break
else:
    # fallback: insert after the suppliers_write_service import block
    raise SystemExit("anchor not found")

f.write_text("".join(lines), encoding="utf-8")
print("done; new line count:", len(lines))
