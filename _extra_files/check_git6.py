import subprocess, os, pathlib, shutil

# First, let's check if git works with explicit env vars
root = pathlib.Path(r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi').resolve()
git_dir = root / '.git'

env = dict(os.environ)
env['GIT_DIR'] = str(git_dir)
env['GIT_WORK_TREE'] = str(root)

# List files in HEAD
result = subprocess.run(['git', 'ls-tree', '-r', '--name-only', 'HEAD'], capture_output=True, env=env)
print(f'ls-tree exit: {result.returncode}')
if result.returncode != 0:
    print(f'Error: {result.stderr.decode().strip()}')
else:
    files = result.stdout.decode().strip().split('\n')
    # Filter for backend files
    backend_files = [f for f in files if f.startswith('backend/') and 'venv' not in f and '__pycache__' not in f]
    print(f'Total backend files in HEAD: {len(backend_files)}')
    for f in backend_files[:10]:
        print(f'  {f}')
    if len(backend_files) > 10:
        print(f'  ... and {len(backend_files) - 10} more')
