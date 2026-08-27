"""Debug script to test import insertion point detection."""
from pathlib import Path

f = Path('modules/customer/routers/accounts.py')
content = f.read_text(encoding='utf-8')
lines = content.split('\n')

# Find import insertion point
i = 0
while i < len(lines):
    stripped = lines[i].strip()
    if not stripped:
        i += 1
        continue
    if stripped.startswith('#'):
        i += 1
        continue
    # Check for module docstring
    if stripped.startswith('"""') or stripped.startswith("'''"):
        # Skip past the docstring
        if stripped.count('"""') < 2 and stripped.count("'''") < 2:
            # Multi-line docstring
            for j in range(i + 1, len(lines)):
                if '"""' in lines[j] or "'''" in lines[j]:
                    i = j + 1
                    break
            else:
                i += 1
        else:
            i += 1
        continue
    break

print('After docstring, i=%d, line=%s' % (i, lines[i][:60]))

# Now find the last import statement
last_import_end = i
in_multiline_import = False

while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    
    # Skip empty lines between imports
    if not stripped:
        i += 1
        continue
    
    # Check for import statements
    if stripped.startswith('import ') or stripped.startswith('from '):
        # Found an import - now find where it ends
        last_import_end = i + 1
        in_multiline_import = '(' in stripped and ')' not in stripped
        print('Import at line %d: %s...' % (i+1, stripped[:60]))
        print('  multiline: %s' % in_multiline_import)
        i += 1
        continue
    
    # Check if we're in a multi-line import
    if in_multiline_import:
        # If line starts with closing paren or is indented, it's part of the import
        if stripped.startswith(')') or stripped == ')' or line.startswith(' ') or line.startswith('\t'):
            last_import_end = i + 1
            print('  continuation at line %d: %s...' % (i+1, stripped[:60]))
            if ')' in stripped:
                in_multiline_import = False
                print('  import ends at line %d' % (i+1))
            i += 1
            continue
        else:
            in_multiline_import = False
            break
    
    # Not an import line - we've moved past imports
    break

print('Insertion point: line %d' % (last_import_end + 1))
if last_import_end < len(lines):
    print('Line at insertion point: %s' % lines[last_import_end][:80])
