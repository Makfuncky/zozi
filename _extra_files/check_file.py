import subprocess

result = subprocess.run(['git', 'show', 'HEAD:backend/routers/admin_treasury.py'], capture_output=True)
content = result.stdout.decode('utf-8', errors='replace')
print(f'HEAD admin_treasury.py: {len(content)} bytes')
print(content[:800])
