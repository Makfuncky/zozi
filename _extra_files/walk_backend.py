import os

backend = 'D:/Projects/10- E-COMMERCE_WEBSITE/zozi/backend'
total_py = 0
total_bytes = 0

for root, dirs, files in os.walk(backend):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    level = root.replace(backend, '').count(os.sep)
    indent = '  ' * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = '  ' * (level + 1)
    py_files = [f for f in files if f.endswith('.py')]
    total_py += len(py_files)
    for f in sorted(py_files):
        full = os.path.join(root, f)
        size = os.path.getsize(full)
        total_bytes += size
        print(f'{subindent}{f} ({size} bytes)')

print(f'\nTotal .py files: {total_py}')
print(f'Total .py bytes: {total_bytes:,}')
