import re
from pathlib import Path

for f in [Path("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend/db/employee_models.py"), Path("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend/db/media_models.py")]:
    text = f.read_text(encoding="utf-8")
    for m in re.finditer(r'__tablename__\s*=\s*"([^"]+)"', text):
        tn = m.group(1)
        nearby = text[m.end():m.end()+500]
        has_schema = "__table_args__" in nearby and "schema" in nearby.lower()
        print(f"{f.name}: {tn} -> schema present nearby: {has_schema}")
