import os, pathlib

# Search entire D: drive for backend/main.py and routers
search_paths = [
    r'D:\Projects\10- E-COMMERCE WEBSITE',
    r'C:\Users\user\Documents',
    r'C:\Users\user\Desktop',
    r'C:\Users\user\source',
    r'C:\temp',
    r'C:\Projects',
]

found = False
for base in search_paths:
    if os.path.exists(base):
        for dirpath, dirnames, filenames in os.walk(base):
            # Skip large dirs
            for d in list(dirnames):
                if d in ['node_modules', 'venv', '__pycache__', '.kilo', '.git', 'bin', 'obj']:
                    dirnames.remove(d)
            for f in filenames:
                if f == 'main.py' and 'backend' in dirpath.lower():
                    full = os.path.join(dirpath, f)
                    size = os.path.getsize(full)
                    print(f'Found backend main.py: {full} ({size} bytes)')
                    found = True
                elif f == 'main.py' and ('backend' in full.lower() or 'zozi' in full.lower()):
                    full = os.path.join(dirpath, f)
                    size = os.path.getsize(full)
                    print(f'Found main.py: {full} ({size} bytes)')
                    found = True
        # Also check for routers directory
        for dirpath, dirnames, filenames in os.walk(base):
            if 'routers' in dirnames:
                full = os.path.join(dirpath, 'routers')
                contents = os.listdir(full)
                py_files = [f for f in contents if f.endswith('.py')]
                print(f'Found routers dir: {full} ({len(py_files)} .py files)')
                found = True
                dirnames.clear()  # Don't recurse further

if not found:
    print('No backend main.py or routers directory found anywhere')
    
# Check for any .bak or .orig files
for base in [r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi']:
    if os.path.exists(base):
        for dirpath, dirnames, filenames in os.walk(base):
            for d in list(dirnames):
                if d in ['node_modules', 'venv', '__pycache__']:
                    dirnames.remove(d)
            for f in filenames:
                if f.endswith('.bak') or f.endswith('.orig'):
                    print(f'Backup file: {os.path.join(dirpath, f)}')

# Check for any git pack files anywhere
import glob
pack_files = glob.glob(r'D:\Projects/10- E-COMMERCE_WEBSITE/**/*.pack', recursive=True)
pack_files += glob.glob(r'D:\Projects/**/*.pack', recursive=True)
if pack_files:
    print(f'\nPack files found: {pack_files}')
else:
    print('No .pack files found')
