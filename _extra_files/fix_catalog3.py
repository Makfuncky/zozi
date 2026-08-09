import io
p = r"backend/models/catalog/products.py"
s = io.open(p, encoding="utf-8").read()
repls = [
    "class ProductImage(Base):",
    "class LogisticsZone(Base):",
    "class LogisticsPricingRule(Base):",
]
for r in repls:
    target = r[:-2] + ", TenantMixin):"
    assert s.count(r) == 1, (r, s.count(r))
    s = s.replace(r, target)
io.open(p, "w", encoding="utf-8").write(s)
print("done")
