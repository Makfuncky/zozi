import os, subprocess, sys

# Change to the correct directory
os.chdir(r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi')
os.chdir('backend')

# Now list everything using PowerShell
print('=== backend/routers/ directory ===')
result = subprocess.run(['powershell', '-Command', 
    'Get-ChildItem -Path "routers" -File | Select-Object -ExpandProperty Name | Sort'],
    capture_output=True, text=True)
flat_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
print(f'Flat .py files: {len(flat_files)}')
for f in flat_files[:30]:
    print(f'  {f}')
if len(flat_files) > 30:
    print(f'  ... and {len(flat_files) - 30} more')

print('\n=== subdirectory check ===')
result2 = subprocess.run(['powershell', '-Command', 
    'Get-ChildItem -Path "routers" -Directory | Select-Object -ExpandProperty Name | Sort'],
    capture_output=True, text=True)
subdirs = [d.strip() for d in result2.stdout.strip().split('\n') if d.strip()]
print(f'Subdirectories in routers/: {len(subdirs)}')
if subdirs:
    print('EXISTS (should have been deleted):')
    for d in subdirs:
        print(f'  {d}/')
else:
    print('All subfolders deleted ✓')

# Check auth.py type
print('\n=== auth.py check ===')
with open('routers/auth.py', 'r') as f:
    auth_content = f.read()
print(f'Size: {len(auth_content)} bytes')
if 'from data.routers_security_auth import' in auth_content:
    print('Type: SHIM (imports from data.routers_security_auth)')
elif 'APIRouter' in auth_content:
    print('Type: FULL IMPLEMENTATION')
    # Find the router definition
    for line in auth_content.split('\n')[:10]:
        if 'router' in line.lower():
            print(f'  {line}')
print(f'First line: {auth_content.split(chr(10))[0]}')
print(f'Last line: {auth_content.split(chr(10))[-2]}')

# Check main.py imports
print('\n=== main.py ws_chat/communication import ===')
with open('main.py', 'r') as f:
    main_content = f.read()
for i, line in enumerate(main_content.split('\n')):
    if 'ws_chat' in line or 'communication' in line.lower():
        print(f'  Line {i+1}: {line.strip()}')

# Check data/ forwarder files
print('\n=== data/ forwarder files ===')
for f in ['routers_security_auth.py', 'routers_hr_governance.py']:
    path = f'data/{f}'
    if os.path.exists(path):
        with open(path, 'r') as fh:
            content = fh.read()
        print(f'{f}: EXISTS ({len(content)} bytes)')
        for line in content.split('\n')[:5]:
            print(f'  {line}')
    else:
        print(f'{f}: MISSING')

# Check supplier_countries_service.py line 473
print('\n=== supplier_countries_service.py line 473 ===')
path = 'services/supplier/supplier_countries_service.py'
if os.path.exists(path):
    with open(path, 'r') as f:
        lines = f.readlines()
    if len(lines) >= 473:
        print(f'Line 473: {lines[472].strip()}')
        if '-' in lines[472].strip() and 'consumer_protection' not in lines[472].strip():
            print('  WARNING: Dangling minus detected')
        else:
            print('  OK: No dangling minus')
    else:
        print(f'File has only {len(lines)} lines')
else:
    print(f'File not found')

# Try to run the app
print('\n=== App load test ===')
os.chdir(r'../')
result = subprocess.run(['python', '-c', 
    'import sys; sys.path.insert(0, "backend"); '
    'import os; os.environ["SECRET_KEY"]="test-key"; '
    'from main import app; '
    'routes = [r for r in app.routes if hasattr(r, "path") and r.path.startswith("/api/v1/")]; '
    'print(f"{len(routes)} API routes loaded")'],
    capture_output=True, text=True, cwd=r'.')
if result.returncode == 0:
    print(result.stdout.strip())
else:
    print(f'Error ({result.returncode}):')
    print(result.stderr[:2000])
