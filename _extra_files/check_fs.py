import os, sys

# Check if the directory exists
backend = r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi\backend'
print(f'backend exists: {os.path.exists(backend)}')
print(f'backend is dir: {os.path.isdir(backend)}')

# List contents
try:
    items = os.listdir(backend)
    print(f'Contents ({len(items)} items):')
    for item in sorted(items):
        full = os.path.join(backend, item)
        is_dir = os.path.isdir(full)
        size = os.path.getsize(full) if not is_dir else '<DIR>'
        print(f'  {item} ({size})')
except Exception as e:
    print(f'Error listing: {e}')

# Check if main.py exists specifically
main_path = os.path.join(backend, 'main.py')
print(f'\nmain.py exists: {os.path.exists(main_path)}')
print(f'main.py is file: {os.path.isfile(main_path)}')

# Check if routers directory exists
routers_path = os.path.join(backend, 'routers')
print(f'routers dir exists: {os.path.exists(routers_path)}')
print(f'routers dir is dir: {os.path.isdir(routers_path)}')

if os.path.isdir(routers_path):
    try:
        items = os.listdir(routers_path)
        print(f'routers contents ({len(items)} items):')
        for item in sorted(items)[:10]:
            print(f'  {item}')
    except Exception as e:
        print(f'Error listing routers: {e}')
