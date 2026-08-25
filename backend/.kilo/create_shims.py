"""Create all missing shim modules and fix imports."""
import os
import re

BASE = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

# Read errors
with open(os.path.join(BASE, ".kilo", "import_errors.txt"), "r") as f:
    lines = f.readlines()

# Extract missing modules and import errors
missing_modules = {}
import_errors = {}
for line in lines:
    if "No module named" in line:
        match = re.search(r"No module named '([^']+)'", line)
        if match:
            mod = match.group(1)
            missing_modules[mod] = missing_modules.get(mod, 0) + 1
    elif "cannot import name" in line:
        match = re.search(r"cannot import name '([^']+)' from '([^']+)'", line)
        if match:
            name, mod = match.group(1), match.group(2)
            if mod not in import_errors:
                import_errors[mod] = []
            import_errors[mod].append(name)

# Define shim modules to create
shims = {
    # domains.comms.services.chat.chat_system
    "domains.comms.services.chat.chat_system": {
        "path": os.path.join(BASE, "domains", "comms", "services", "chat", "chat_system.py"),
        "content": '''"""Chat system re-export shim."""\nfrom __future__ import annotations\nfrom domains.comms.services.messaging.chat.chat_read_service import *\nfrom domains.comms.services.messaging.chat.chat_write_service import *\n'''
    },
}

# Create directories and files
for mod, config in shims.items():
    path = config["path"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(config["content"])
    print(f"Created: {path}")

# Print missing modules for reference
print("\n=== Missing Modules ===")
for mod, count in sorted(missing_modules.items(), key=lambda x: x[1], reverse=True):
    print(f"{count}: {mod}")

print("\n=== Import Errors ===")
for mod, names in sorted(import_errors.items()):
    print(f"{mod}: {names}")
