import subprocess, os, pathlib

# Get absolute paths
root = pathlib.Path('.').resolve()
git_dir = root / '.git'

env = dict(os.environ)
env['GIT_DIR'] = str(git_dir)
env['GIT_WORK_TREE'] = str(root)

# Try git stash show
result = subprocess.run(
    ['git', 'stash', 'list'],
    capture_output=True, env=env
)
print(f'Stash list exit: {result.returncode}')
print(f'stdout: {result.stdout.decode().strip()[:200]}')
print(f'stderr: {result.stderr.decode().strip()[:200]}')

# Try git show
result2 = subprocess.run(
    ['git', 'show', 'stash@{0}:backend/routers/security/auth.py'],
    capture_output=True, env=env
)
print(f'\nShow exit: {result2.returncode}')
if result2.returncode == 0:
    content = result2.stdout.decode('utf-8', errors='replace')
    print(f'Size: {len(content)} bytes')
    with open('auth_security_original.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Saved to auth_security_original.py')
    print('First 500 chars:')
    print(content[:500])
else:
    err = result2.stderr.decode('utf-8', errors='replace')
    print(f'Error: {err}')
