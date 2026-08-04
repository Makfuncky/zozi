import os, sys

# Direct checks
backend = r'D:\Projects/10- E-COMMERCE_WEBSITE/zozi/backend'
main_py = os.path.join(backend, 'main.py')
routers = os.path.join(backend, 'routers')

print(f'os.path.exists(main_py): {os.path.exists(main_py)}')
print(f'os.path.getsize(main_py): {os.path.getsize(main_py) if os.path.exists(main_py) else "N/A"}')

print(f'\nos.path.exists(routers): {os.path.exists(routers)}')
print(f'os.path.isdir(routers): {os.path.isdir(routers)}')

if os.path.exists(routers):
    items = os.listdir(routers)
    print(f'routers contents: {len(items)} items')
    print(f'First 10: {sorted(items)[:10]}')
    py_count = sum(1 for f in items if f.endswith('.py'))
    print(f'.py files: {py_count}')

# Try with pathlib
import pathlib
p = pathlib.Path(backend)
print(f'\npathlib Path(backend).exists(): {p.exists()}')
print(f'pathlib Path(backend).iterdir():')
try:
    for item in sorted(p.iterdir()):
        print(f'  {item.name}')
except Exception as e:
    print(f'  Error: {e}')

# Check the stat of the routers directory
r = pathlib.Path(routers)
print(f'\npathlib Path(routers).exists(): {r.exists()}')
if r.exists():
    print(f'pathlib Path(routers).is_dir(): {r.is_dir()}')
    items = list(r.iterdir())
    print(f'Items: {len(items)}')
    for item in sorted(items)[:10]:
        if item.is_file():
            print(f'  {item.name} ({item.stat().st_size} bytes)')
        elif item.is_dir():
            print(f'  {item.name}/ ({len(list(item.iterdir()))} items)')

# Check using subprocess
import subprocess
result = subprocess.run(['cmd', '/c', 'dir', backend], capture_output=True, text=True)
print(f'\nCMD dir {backend}:')
print(result.stdout)
print(result.stderr)
