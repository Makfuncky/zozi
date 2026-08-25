import re

with open(r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\.kilo\import_errors.txt', 'r') as f:
    lines = f.readlines()

modules = {}
for line in lines:
    if 'No module named' in line:
        match = re.search(r"No module named '([^']+)'", line)
        if match:
            mod = match.group(1)
            modules[mod] = modules.get(mod, 0) + 1

sorted_modules = sorted(modules.items(), key=lambda x: x[1], reverse=True)
for mod, count in sorted_modules:
    print(f"{count}: {mod}")
