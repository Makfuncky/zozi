import sys
sys.path.insert(0, r"F:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")

import db.models as m
model_names = sorted([n for n in dir(m) if not n.startswith("_")])
print(f"db.models exports {len(model_names)} names:")
print(", ".join(model_names))

