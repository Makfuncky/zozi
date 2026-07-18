"""Fix all dict-style current_user accesses to attribute-style in both controllers."""
import re

def fix_file(path):
    content = open(path, encoding='utf-8').read()
    original = content

    # Fix current_user.get("id") and current_user.get('id') etc.
    replacements = [
        (r"current_user\.get\(['\"]id['\"]\)", "current_user.id"),
        (r"current_user\.get\(['\"]role['\"]\)", "current_user.role"),
        (r"current_user\.get\(['\"]username['\"]\)", "current_user.username"),
        (r"current_user\.get\(['\"]email['\"]\)", "current_user.email"),
        (r"current_user\.get\(['\"]phone['\"]\)", "current_user.phone"),
        (r"current_user\.get\(['\"]is_active['\"]\)", "current_user.is_active"),
        # Fix bracket style
        (r"current_user\[['\"](id)['\"]\]", "current_user.id"),
        (r"current_user\[['\"](role)['\"]\]", "current_user.role"),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    if content != original:
        open(path, 'w', encoding='utf-8').write(content)
        # Count what was replaced
        for pattern, replacement in replacements:
            matches = len(re.findall(pattern, original))
            if matches:
                print(f"  {path}: {matches}x '{pattern}' -> '{replacement}'")
    else:
        print(f"  {path}: no changes")

fix_file('controllers/supplier_controller.py')
fix_file('controllers/admin_controller.py')

# Verify remaining dict accesses
for path in ['controllers/supplier_controller.py', 'controllers/admin_controller.py']:
    content = open(path, encoding='utf-8').read()
    remaining_get = re.findall(r"current_user\.get\('[^']+'\)", content) + re.findall(r'current_user\.get\("[^"]+"\)', content)
    remaining_bracket = re.findall(r"current_user\['[^']+'\]", content) + re.findall(r'current_user\["[^"]+"\]', content)
    non_permissions = [x for x in remaining_get if 'permissions' not in x]
    print(f"\n{path}:")
    print(f"  Remaining .get(): {len(remaining_get)} ({remaining_get[:5]})")
    print(f"  Remaining []: {len(remaining_bracket)}")

