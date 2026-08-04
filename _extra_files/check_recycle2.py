import os, pathlib, time

# Check the user-owned recycle bin on D:
rec_bin = r'D:\$Recycle.Bin\S-1-5-21-1339371623-4152739331-235715422-1002'
print(f'Checking: {rec_bin}')
print(f'Exists: {os.path.exists(rec_bin)}')

if os.path.exists(rec_bin):
    try:
        items = os.listdir(rec_bin)
        print(f'Items: {len(items)}')
        for item in items[:30]:
            full = os.path.join(rec_bin, item)
            try:
                s = os.stat(full)
                size_mb = s.st_size / (1024 * 1024)
                mtime = time.ctime(s.st_mtime)
                # Check if it's a directory (recycled folders show as $I + $R files)
                is_dir = os.path.isdir(full)
                print(f'  {item}: size={size_mb:.2f}MB, mtime={mtime}, is_dir={is_dir}')
            except Exception as e:
                print(f'  {item}: ERROR {e}')
    except PermissionError as e:
        print(f'Permission denied: {e}')
        # Try with different approach
        import subprocess
        result = subprocess.run(
            ['cmd', '/c', 'dir', rec_bin, '/a'],
            capture_output=True, text=True
        )
        print(f'CMD dir output:\n{result.stdout[:2000]}')
        print(f'CMD error:\n{result.stderr[:500]}')
