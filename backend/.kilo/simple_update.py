import os
import re
from pathlib import Path

# Simplified mappings - only the most critical ones
MAPPINGS = {
    "domains.hr.services.compliance.coi_service": "domains.hr.services.compliance.coi_service",
    "domains.promotions.services.coupons.coupons_service": "domains.promotions.services.coupons.coupons_service",
    "domains.orders.services.cart.cart_service": "domains.orders.services.cart.cart_service",
    "domains.accounts.services.addresses.addresses_service": "domains.accounts.services.addresses.addresses_service",
}

def update_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return 0
    
    original = content
    for old, new in MAPPINGS.items():
        content = content.replace(old, new)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return 1
    return 0

total = 0
for f in Path("backend").rglob("*.py"):
    if "__pycache__" not in str(f):
        total += update_file(str(f))

print(f"Updated {total} files")
