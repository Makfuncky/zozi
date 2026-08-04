import subprocess, os

# Try git init in a new repo and copy the file
# Actually, let's try a different approach - use Python to read git objects directly
# First, check what's in .git/objects
objects = os.listdir('.git/objects')
print(f'Object dirs: {sorted(objects)[:20]}')

# Check if refs/heads/main exists
ref_path = '.git/refs/heads/main'
if os.path.exists(ref_path):
    with open(ref_path) as f:
        commit = f.read().strip()
    print(f'HEAD commit: {commit}')
else:
    print('No refs/heads/main')

# Check logs/HEAD for stash info
logs_path = '.git/logs/HEAD'
if os.path.exists(logs_path):
    with open(logs_path) as f:
        lines = f.readlines()
    print(f'HEAD logs: {len(lines)} entries')
    for line in lines[:10]:
        print(line.strip()[:200])
else:
    print('No logs/HEAD')

# Check logs/refs/stash
stash_log = '.git/logs/refs/stash'
if os.path.exists(stash_log):
    with open(stash_log) as f:
        lines = f.readlines()
    print(f'Stash log: {len(lines)} entries')
    for line in lines:
        print(line.strip()[:200])
else:
    print('No stash log')
