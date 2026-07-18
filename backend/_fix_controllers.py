import re

for filepath in ['controllers/supplier_controller.py', 'controllers/admin_controller.py']:
    content = open(filepath, encoding='utf-8').read()
    # Find all unique current_user.get(...) patterns
    patterns = sorted(set(re.findall(r"current_user\.get\('[^']+'\)", content) +
                          re.findall(r'current_user\.get\("[^"]+"\)', content)))
    print(f"\n=== {filepath} ===")
    for p in patterns:
        print(" ", p)
    # Also dict-style
    brackets = sorted(set(re.findall(r"current_user\['[^']+'\]", content) +
                          re.findall(r'current_user\["[^"]+"\]', content)))
    for b in brackets:
        print("  BRACKET:", b)

