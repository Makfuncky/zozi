import subprocess, sys, os

# Get the git root
result = subprocess.run(
    ['git', 'rev-parse', '--git-dir'],
    capture_output=True,
    cwd=r'D:\Projects\10- E-COMMERCE WEBSITE\zozi'
)
print(f'Git dir: {result.stdout.decode().strip()}')
print(f'Error: {result.stderr.decode().strip()}')

# Try showing the file from stash
result2 = subprocess.run(
    ['git', 'show', 'stash@{0}:backend/routers/security/auth.py'],
    capture_output=True,
    cwd=r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi'
)
print(f'\nShow result: exit={result2.returncode}')
if result2.returncode == 0:
    content = result2.stdout.decode('utf-8', errors='replace')
    print(f'Size: {len(content)} bytes')
    with open('auth_security_original.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Saved to auth_security_original.py')
else:
    print(f'STDERR: {result2.stderr.decode().strip()}')
