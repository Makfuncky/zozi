import subprocess
result = subprocess.run(['git', 'show', 'HEAD:backend/routers/security/auth.py'], capture_output=True)
if result.returncode == 0:
    content = result.stdout.decode('utf-8', errors='replace')
    print(f'Size: {len(content)} bytes')
    print('=== First 2000 chars ===')
    print(content[:2000])
else:
    print(f'Exit code: {result.returncode}')
    print(result.stderr.decode('utf-8', errors='replace'))
