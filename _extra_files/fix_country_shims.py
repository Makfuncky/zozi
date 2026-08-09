#!/usr/bin/env python3
"""Fix remaining country→geography shim files."""
import os
import sys

os.chdir(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")

failed_shims = [
    ("services/country/confidence_scoring.py", "services.geography.confidence_scoring"),
    ("services/country/country_ai_research.py", "services.geography.country_ai_research"),
    ("services/country/country_data_orchestrator.py", "services.geography.country_data_orchestrator"),
    ("services/country/country_detection.py", "services.geography.country_detection"),
    ("services/country/country_router_service.py", "services.geography.country_router_service"),
    ("services/country/country_write_service.py", "services.geography.country_write_service"),
]

for shim_rel, dst_module in failed_shims:
    shim_content = '"""Backward-compat shim: re-export from %s"""\n' % dst_module
    shim_content += "from %s import *  # noqa: F401,F403\n" % dst_module
    shim_dir = os.path.dirname(shim_rel)
    os.makedirs(shim_dir, exist_ok=True)
    with open(shim_rel, "w", encoding="utf-8") as f:
        f.write(shim_content)
    print("Created shim: %s" % shim_rel)

# Verify the services/country/__init__.py shim
init_path = os.path.join("services", "country", "__init__.py")
if os.path.exists(init_path):
    with open(init_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "services.geography" not in content:
        with open(init_path, "w", encoding="utf-8") as f:
            f.write('"""Backward-compat shim: re-export from services.geography"""\n')
            f.write("from services.geography import *  # noqa: F401,F403\n")
        print("Fixed services/country/__init__.py")
    else:
        print("services/country/__init__.py already correct")
else:
    os.makedirs("services/country", exist_ok=True)
    with open(init_path, "w", encoding="utf-8") as f:
        f.write('"""Backward-compat shim: re-export from services.geography"""\n')
        f.write("from services.geography import *  # noqa: F401,F403\n")
    print("Created services/country/__init__.py")

print("\nAll shims fixed!")
