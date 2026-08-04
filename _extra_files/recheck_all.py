import os, pathlib

# Check if .git was a real repo or if there are pack files
root = pathlib.Path(r'D:\Projects/10- E-COMMERCE_WEBSITE/zozi')
print(f'Root: {root}')
print(f'Root contents: {sorted(os.listdir(root))}')

# Check for any hidden directories
for item in sorted(os.listdir(root)):
    full = root / item
    if item.startswith('.') or item == 'backend':
        print(f'\n{item}:')
        if full.is_dir():
            print(f'  is_dir: True')
            print(f'  contents: {sorted(os.listdir(full))}')
        else:
            print(f'  is_file: True, size: {full.stat().st_size}')

# Check backend contents
backend = root / 'backend'
if backend.exists():
    print(f'\nbackend contents: {sorted(os.listdir(backend))}')
    for item in os.listdir(backend):
        full = backend / item
        if full.is_dir():
            print(f'  {item}/ contents: {sorted(os.listdir(full))}')
        else:
            print(f'  {item} ({full.stat().st_size} bytes)')

# Look for any backup files
print('\n Searching for .bak, .orig, .backup files:')
for dirpath, dirnames, filenames in os.walk(root):
    for d in list(dirnames):
        if 'node_modules' in d or 'venv' in d or '__pycache__' in d or '.kilo' in d:
            dirnames.remove(d)
    for f in filenames:
        if '.bak' in f or '.orig' in f or '.backup' in f or '.old' in f:
            print(f'  {os.path.join(dirpath, f)}')
