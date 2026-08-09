import subprocess
orig = subprocess.check_output(
    ["git","show","HEAD:backend/models/catalog/products.py"],
).decode("utf-8")
p = r"backend\models\catalog\products.py"
old = (
    'class Product(Base, TenantMixin):\n'
    '    __tablename__ = "products"\n'
    '    __table_args__ = ({"schema": "commerce"},)'
)
assert old in orig, "Product anchor not found"
assert orig.count(old) == 1, "anchor not unique"
new = (
    'class Product(Base, TenantMixin):\n'
    '    __tablename__ = "products"\n'
    '    __table_args__ = (\n'
    '        Index("ix_products_materials_gin", "materials", postgresql_using="gin"),\n'
    '        Index("ix_products_images_gin", "images", postgresql_using="gin"),\n'
    '        Index("ix_products_tags_gin", "tags", postgresql_using="gin"),\n'
    '        Index("ix_products_attributes_gin", "attributes", postgresql_using="gin"),\n'
    '        Index("ix_products_filter_attributes_gin", "filter_attributes", postgresql_using="gin"),\n'
    '        Index("ix_products_variant_axes_gin", "variant_axes", postgresql_using="gin"),\n'
    '        Index("ix_products_country_created", "country_code", "created_at"),\n'
    '        {"schema": "commerce"},\n'
    '    )'
)
s = orig.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("OK: Product-specific GIN+composite applied; all other classes untouched")
