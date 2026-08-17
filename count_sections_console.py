import re
from collections import Counter

with open('run3.log', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the table in console output
lines = content.splitlines()
in_table = False
sections = []
for line in lines:
    if line.startswith('| # | Section |'):
        in_table = True
        continue
    if in_table:
        if line.startswith('|---') or not line.startswith('|'):
            in_table = False
            continue
        parts = line.split('|')
        if len(parts) > 3:
            sec = parts[2].strip()
            if sec.startswith('§'):
                sections.append(sec)

c = Counter(sections)
for sec in ["§I", "§II", "§III", "§IV", "§V", "§VI"]:
    print(f"{sec}: {c.get(sec, 0)}")
print(f"Total: {sum(c.values())}")
