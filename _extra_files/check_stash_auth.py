import subprocess, sys

# Try to get the file from git stash
result = subprocess.run(
    ['git', 'show', 'stash@{0}:backend/routers/security/auth.py'],
    capture_output=True
)
print(f'Exit code: {result.returncode}')
if result.returncode == 0:
    content = result.stdout.decode('utf-8', errors='replace')
    print(f'Size: {len(content)} bytes')
    print(content[:2000])
else:
    print('STDERR:', result.stderr.decode('utf-8', errors='replace'))
