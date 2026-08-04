import subprocess, os

env = dict(os.environ)
env['GIT_DIR'] = os.path.abspath('.git')
env['GIT_WORK_TREE'] = os.path.abspath('.')
result = subprocess.run(['git', 'show', 'stash@{0}:backend/routers/security/auth.py'], capture_output=True, env=env)
print(f'Exit: {result.returncode}')
if result.returncode == 0:
    content = result.stdout.decode('utf-8', errors='replace')
    print(f'Size: {len(content)} bytes')
    with open('auth_security_original.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Saved to auth_security_original.py')
    print('First 1000 chars:')
    print(content[:1000])
else:
    err = result.stderr.decode('utf-8', errors='replace')
    print(f'Error: {err}')
