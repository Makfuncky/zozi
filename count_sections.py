import re
from collections import Counter

with open('documents/FEATURE_TRACKER.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

sections = []
for line in lines:
    m = re.match(r'^\| ([0-9]+) \| (§[IVX]+) \|', line)
    if m:
        sections.append(m.group(2))

c = Counter(sections)
for sec in ["§I", "§II", "§III", "§IV", "§V", "§VI"]:
    print(f"{sec}: {c.get(sec, 0)}")
print(f"Total: {sum(c.values())}")
