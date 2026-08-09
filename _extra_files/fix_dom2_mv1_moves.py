#!/usr/bin/env python3
"""
Fix DOM2 (wrong domain folder) and MV1 (mis-housed files) audit findings.

Moves 15 files to their correct domain folders, updates all imports,
and creates backward-compat shims so nothing breaks.
"""
import os
import shutil

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

def move_file(src_rel, dst_rel, shims=None):
    """Move src to dst and create backward-compat shim if importers exist."""
    src = os.path.join(BACKEND, src_rel)
    dst = os.path.join(BACKEND, dst_rel)
    
    if not os.path.exists(src):
        print(f"  SKIP (not found): {src_rel}")
        return
    
    # Ensure destination dir exists
    dst_dir = os.path.dirname(dst)
    os.makedirs(dst_dir, exist_ok=True)
    init_file = os.path.join(dst_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            pass
    
    # Move the file
    shutil.copy2(src, dst)
    print(f"  MOVED: {src_rel} -> {dst_rel}")
    
    # Create backward-compat shim if there are importers
    if shims:
        with open(dst, "r", encoding="utf-8") as f:
            content = f.read()
        
        # For providers moved to subfolders, create shim at old location
        for old_module, new_module in shims:
            old_path = os.path.join(BACKEND, old_module.replace(".", "/") + ".py")
            old_dir = os.path.dirname(old_path)
            os.makedirs(old_dir, exist_ok=True)
            
            # Read the new file to get all public names
            with open(dst, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Extract all public names (classes, functions, constants)
            public_names = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("def ") or stripped.startswith("async def "):
                    name = stripped.split("(")[0].replace("def ", "").strip()
                    if not name.startswith("_"):
                        public_names.append(name)
                elif stripped.startswith("class "):
                    name = stripped.split("(")[0].split(":")[0].replace("class ", "").strip()
                    if not name.startswith("_"):
                        public_names.append(name)
                elif stripped.startswith("__all__"):
                    # Parse __all__ list
                    import ast
                    try:
                        all_names = ast.literal_eval(stripped.split("=", 1)[1].strip())
                        public_names.extend(all_names)
                    except:
                        pass
            
            # Remove duplicates
            public_names = list(dict.fromkeys(public_names))
            
            # Write shim
            shim_lines = [
                f'"""Backward-compat shim: {old_module} -> {new_module}"""\n',
                f"from {new_module} import (\n",
            ]
            for name in public_names:
                shim_lines.append(f"    {name},\n")
            shim_lines.append(")\n")
            shim_lines.append(f"__all__ = {repr(public_names)}\n")
            
            with open(old_path, "w", encoding="utf-8") as f:
                f.writelines(shim_lines)
            print(f"  SHIM: {old_module} -> {new_module}")

def update_import_in_file(filepath, old_module, new_module):
    """Replace old_module with new_module in a file's imports."""
    if not os.path.exists(filepath):
        return False
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    if old_module not in content:
        return False
    
    # Replace both "from old_module import X" and "import old_module"
    new_content = content.replace(old_module, new_module)
    
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"  UPDATED IMPORT: {os.path.relpath(filepath, BACKEND)}")
        return True
    return False

print("=" * 70)
print("DOM2/MV1 FILE PLACEMENT FIX")
print("=" * 70)

# ═══════════════════════════════════════════════════════════════════════
# GROUP 1: PROVIDERS moves (DOM2 + MV1)
# ═══════════════════════════════════════════════════════════════════════
print("\n--- GROUP 1: Provider file moves ---")

# 1. providers/logistics/geo.py -> providers/geography/geo.py (DOM2)
print("\n1. providers/logistics/geo.py -> providers/geography/geo.py")
move_file("providers/logistics/geo.py", "providers/geography/geo.py")

# 2. providers/catalog/text.py -> providers/ai/text.py (DOM2)
print("\n2. providers/catalog/text.py -> providers/ai/text.py")
move_file("providers/catalog/text.py", "providers/ai/text.py")

# 3. providers/ocr.py -> providers/ai/ocr.py (MV1) - has importers
print("\n3. providers/ocr.py -> providers/ai/ocr.py (has importers)")
move_file("providers/ocr.py", "providers/ai/ocr.py",
          shims=[("providers.ocr", "providers.ai.ocr")])
# Update importers
for importer in [
    os.path.join(BACKEND, "providers/ai/mcp_server.py"),
    os.path.join(BACKEND, "providers/ai/async_workers.py"),
]:
    update_import_in_file(importer, "from providers.ocr", "from providers.ai.ocr")

# 4. providers/vision.py -> providers/ai/vision.py (MV1) - has importers
print("\n4. providers/vision.py -> providers/ai/vision.py (has importers)")
move_file("providers/vision.py", "providers/ai/vision.py",
          shims=[("providers.vision", "providers.ai.vision")])
for importer in [
    os.path.join(BACKEND, "providers/ai/mcp_server.py"),
    os.path.join(BACKEND, "providers/ai/async_workers.py"),
]:
    update_import_in_file(importer, "from providers.vision", "from providers.ai.vision")

# 5. providers/voice_to_text.py -> providers/ai/voice_to_text.py (MV1)
print("\n5. providers/voice_to_text.py -> providers/ai/voice_to_text.py")
move_file("providers/voice_to_text.py", "providers/ai/voice_to_text.py",
          shims=[("providers.voice_to_text", "providers.ai.voice_to_text")])

# 6. providers/bg_remover.py -> providers/media/bg_remover.py (MV1) - has importers
print("\n6. providers/bg_remover.py -> providers/media/bg_remover.py (has importers)")
move_file("providers/bg_remover.py", "providers/media/bg_remover.py",
          shims=[("providers.bg_remover", "providers.media.bg_remover")])
# Update data/ shim
update_import_in_file(
    os.path.join(BACKEND, "data/providers_bg_remover.py"),
    "from providers.bg_remover", "from providers.media.bg_remover"
)

# 7. providers/image.py -> providers/media/image.py (MV1)
print("\n7. providers/image.py -> providers/media/image.py")
move_file("providers/image.py", "providers/media/image.py",
          shims=[("providers.image", "providers.media.image")])

# ═══════════════════════════════════════════════════════════════════════
# GROUP 2: SERVICES moves (DOM2 + MV1)
# ═══════════════════════════════════════════════════════════════════════
print("\n--- GROUP 2: Service file moves ---")

# 8. services/finance/automation_read_service.py -> services/ai/ (DOM2)
print("\n8. services/finance/automation_read_service.py -> services/ai/")
move_file("services/finance/automation_read_service.py",
          "services/ai/automation_read_service.py")
update_import_in_file(
    os.path.join(BACKEND, "routers/api_finance_automation.py"),
    "from services.finance.automation_read_service",
    "from services.ai.automation_read_service"
)

# 9. services/catalog/wishlist_read_service.py -> services/commerce/ (DOM2)
print("\n9. services/catalog/wishlist_read_service.py -> services/commerce/")
move_file("services/catalog/wishlist_read_service.py",
          "services/commerce/wishlist_read_service.py")

# 10. services/customer/customer_router_service.py -> services/commerce/ (DOM2)
print("\n10. services/customer/customer_router_service.py -> services/commerce/")
move_file("services/customer/customer_router_service.py",
          "services/commerce/customer_router_service.py")
update_import_in_file(
    os.path.join(BACKEND, "routers/api_customer_routes.py"),
    "from services.customer.customer_router_service",
    "from services.commerce.customer_router_service"
)

# 11. services/commerce/cross_border_tracker.py -> services/geography/ (DOM2)
print("\n11. services/commerce/cross_border_tracker.py -> services/geography/")
move_file("services/commerce/cross_border_tracker.py",
          "services/geography/cross_border_tracker.py")

# 12. services/location/geo_service.py -> services/geography/ (DOM2)
print("\n12. services/location/geo_service.py -> services/geography/")
move_file("services/location/geo_service.py",
          "services/geography/geo_service.py")

# 13. services/logistics/geo_fence_service.py -> services/geography/ (DOM2)
print("\n13. services/logistics/geo_fence_service.py -> services/geography/")
move_file("services/logistics/geo_fence_service.py",
          "services/geography/geo_fence_service.py")

# 14. services/commerce/cart_write_service.py -> services/orders/ (DOM2)
print("\n14. services/commerce/cart_write_service.py -> services/orders/")
move_file("services/commerce/cart_write_service.py",
          "services/orders/cart_write_service.py")
update_import_in_file(
    os.path.join(BACKEND, "controllers/orders/cart_controller.py"),
    "from services.commerce.cart_write_service",
    "from services.orders.cart_write_service"
)

# 15. services/country_read_service.py -> services/geography/ (MV1)
print("\n15. services/country_read_service.py -> services/geography/")
move_file("services/country_read_service.py",
          "services/geography/country_read_service.py")
update_import_in_file(
    os.path.join(BACKEND, "controllers/country/country_controller.py"),
    "from services.country_read_service",
    "from services.geography.country_read_service"
)

print("\n" + "=" * 70)
print("ALL MOVES COMPLETE")
print("=" * 70)
