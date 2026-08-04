import subprocess
result = subprocess.run(['git', 'show', 'HEAD:backend/routers/auth.py'], capture_output=True)
print(result.stdout.decode('utf-8', errors='replace'))
