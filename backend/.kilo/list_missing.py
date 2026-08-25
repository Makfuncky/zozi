"""Create shim modules for missing imports."""
import os
import re

BASE = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

# Read errors
with open(os.path.join(BASE, ".kilo", "import_errors.txt"), "r") as f:
    lines = f.readlines()

# Extract missing modules
missing_modules = {}
for line in lines:
    if "No module named" in line:
        match = re.search(r"No module named '([^']+)'", line)
        if match:
            mod = match.group(1)
            missing_modules[mod] = missing_modules.get(mod, 0) + 1

# Print sorted by frequency
for mod, count in sorted(missing_modules.items(), key=lambda x: x[1], reverse=True):
    print(f"{count}: {mod}")
