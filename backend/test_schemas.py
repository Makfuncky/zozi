import sys
sys.path.insert(0, r"F:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
try:
    import db.schemas as s
    names = [n for n in dir(s) if not n.startswith("_")]
    print(f"schemas.py imports OK. Exported {len(names)} names.")
    print("Names:", ", ".join(sorted(names)))
except Exception as e:
    import traceback
    print(f"ERROR importing schemas: {e}")
    print(traceback.format_exc())

