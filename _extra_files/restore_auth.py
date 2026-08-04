import subprocess, os, pathlib

root = pathlib.Path(r'.').resolve()
git_dir = root / '.git'

env = dict(os.environ)
env['GIT_DIR'] = str(git_dir)
env['GIT_WORK_TREE'] = str(root)

result = subprocess.run(
    ['git', 'show', 'stash@{0}:backend/routers/security/auth.py'],
    capture_output=True, env=env
)

if result.returncode == 0:
    content = result.stdout.decode('utf-8', errors='replace')
    print(f'Size: {len(content)} bytes')
    # Write to backend/routers/auth.py (overwrite the re-export shim)
    target = pathlib.Path('backend/routers/auth.py')
    target.write_bytes(result.stdout)
    print(f'Written to {target}')
    # Show first 500 chars
    print(content[:500])
else:
    err = result.stderr.decode('utf-8', errors='replace')
    print(f'Error: {err}')
