"""Replace the bulk_inventory_adjust stub definition with a re-export."""
from pathlib import Path

p = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\controllers\supplier\inventory.py")
txt = p.read_text(encoding="utf-8")
old = (
    "def bulk_inventory_adjust(db: Session, supplier_id: int, adjustments: List[Any]) -> Optional[Any]:\n"
    "    return None\n"
)
new = (
    "# Re-export the canonical implementation from supplier_controller instead of\n"
    "# redefining it (avoids a duplicate symbol definition across modules).\n"
    "from .supplier_controller import bulk_inventory_adjust  # noqa: E402,F401\n"
)
assert old in txt, "stub definition not found"
txt = txt.replace(old, new)
with open(p, "w", encoding="utf-8", newline="") as f:
    f.write(txt)
print("updated inventory.py")
