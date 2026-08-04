import subprocess, os

# Try various ways to access git
env = dict(os.environ)
env['GIT_DIR'] = os.path.abspath('.git')
env['GIT_WORK_TREE'] = os.path.abspath('.')

# List stash
result = subprocess.run(['git', 'stash', 'list'], capture_output=True, text=True, env=env)
print(f'Stash list exit: {result.returncode}')
print(f'Stdout: {result.stdout.strip()}')
print(f'Stderr: {result.stderr.strip()}')

# Try to show the file from stash
result2 = subprocess.run(
    ['git', 'show', 'stash@{0}:backend/routers/security/auth.py'],
    capture_output=True,
    env=env
)
print(f'\nShow stash exit: {result2.returncode}')
if result2.returncode == 0:
    content = result2.stdout.decode('utf-8', errors='replace')
    print(f'Size: {len(content)} bytes')
    with open('auth_security_original.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Saved!')
    print(content[:500])
else:
    print(f'Error: {result2.stderr.decode("utf-8", errors="replace").strip()}')
