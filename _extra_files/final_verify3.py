import os, subprocess, sys

root = r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi'

# Try multiple approaches to list files
print('=== PowerShell with ForwardSlash path ===')
result = subprocess.run(['powershell', '-Command', 
    'Get-ChildItem -Path "backend/routers" -File -Recurse | ForEach-Object { $_.FullName }'],
    capture_output=True, text=True, cwd=root, shell=False)
print(f'Exit: {result.returncode}')
print(f'Stdout length: {len(result.stdout)}')
if result.stdout.strip():
    files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    print(f'Found {len(files)} files')
    for f in files[:10]:
        print(f'  {f}')
else:
    print(f'No files found')
    print(f'Stderr: {result.stderr[:500]}')

# Also try with cmd
print('\n=== CMD with ForwardSlash path ===')
result2 = subprocess.run(['cmd', '/c', 'dir "backend/routers/" /s /b'],
    capture_output=True, text=True, cwd=root)
print(f'Exit: {result2.returncode}')
print(f'Stdout: {result2.stdout[:2000]}')
if result2.stderr:
    print(f'Stderr: {result2.stderr[:500]}')

# Try with os.listdir and the working directory trick
print('\n=== Python chdir + os.listdir ===')
os.chdir(root)
os.chdir('backend')
print(f'CWD: {os.getcwd()}')
try:
    items = os.listdir('routers')
    print(f'Routers dir: {len(items)} items')
    dirs = [d for d in items if os.path.isdir('routers/' + d)]
    files = [f for f in items if os.path.isfile('routers/' + f)]
    print(f'  Subdirs: {sorted(dirs)}')
    print(f'  Files: {len(files)}')
    for f in sorted(files)[:10]:
        size = os.path.getsize(f'routers/{f}')
        print(f'    {f} ({size} bytes)')
except Exception as e:
    print(f'Error: {e}')
