import os, subprocess, sys

root = r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi'

# List files using PowerShell with correct cwd
result = subprocess.run(['powershell', '-Command', 
    'Get-ChildItem -Path "backend\\routers" -File -Recurse | Select-Object -ExpandProperty FullName'],
    capture_output=True, text=True, cwd=root)

if result.returncode == 0 and result.stdout.strip():
    files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    print(f'Total .py files in routers/: {len(files)}')
    
    dirs = set()
    flat = []
    subdirs_content = {}
    for f in files:
        p = f.replace(root + '\\', '').replace(root + '/', '').replace('backend\\routers\\', '')
        if '\\' in p:
            sub = p.split('\\')[0]
            dirs.add(sub)
            subdirs_content.setdefault(sub, []).append(p.split('\\')[1])
        else:
            flat.append(p)
    
    print(f'Flat files: {len(flat)}')
    print(f'Subdirectories: {len(dirs)}')
    if dirs:
        print('Subdirs with content:')
        for d in sorted(dirs):
            print(f'  {d}/ ({len(subdirs_content[d])} files)')
