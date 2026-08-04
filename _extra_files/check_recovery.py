import os, sys

root = 'D:/Projects/10- E-COMMERCE_WEBSITE/zozi'
backend = os.path.join(root, 'backend')

print(f'cwd: {os.getcwd()}')
print(f'root exists: {os.path.exists(root)}')
print(f'backend exists: {os.path.exists(backend)}')
print(f'backend is_dir: {os.path.isdir(backend)}')

if os.path.exists(backend):
    print(f'backend contents: {os.listdir(backend)}')

# Check if .git exists
git_dir = os.path.join(root, '.git')
print(f'\n.git exists: {os.path.exists(git_dir)}')
print(f'.git is_dir: {os.path.isdir(git_dir)}')

# Walk the directory tree from root
print(f'\nWalking from root:')
for dirpath, dirnames, filenames in os.walk(root):
    # Skip large dirs
    for d in list(dirnames):
        full = os.path.join(dirpath, d)
        if 'node_modules' in d or 'venv' in d or '__pycache__' in d or '.kilo' in d:
            dirnames.remove(d)
        elif d == 'experiments':
            # Keep but limit
            pass
    for f in filenames:
        if f.endswith('.py'):
            rel = os.path.relpath(os.path.join(dirpath, f), root)
            if 'backend' in rel:
                print(f'  BACKEND: {rel}')
        elif f == 'main.py':
            rel = os.path.relpath(os.path.join(dirpath, f), root)
            print(f'  main.py: {rel}')

# Check for any backup or copy of main.py
import glob
for pattern in ['*/main.py', '**/main.py', '*main.py']:
    matches = glob.glob(os.path.join(root, pattern), recursive=True)
    for m in matches[:10]:
        size = os.path.getsize(m)
        print(f'Found: {os.path.relpath(m, root)} ({size} bytes)')

# Check experiments dir
exp = os.path.join(root, 'experiments')
if os.path.exists(exp):
    print(f'\nExperiments dir exists: {os.listdir(exp)[:5]}...')
