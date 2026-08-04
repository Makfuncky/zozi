import os, pathlib

# Check various recycle bin locations
locations = [
    r'C:\Recycle.Bin',
    r'D:\Recycle.Bin',
    r'C:\$Recycle.Bin',
    r'D:\$Recycle.Bin',
]

for loc in locations:
    try:
        exists = os.path.exists(loc)
        is_dir = os.path.isdir(loc)
        print(f'{loc}: exists={exists}, is_dir={is_dir}')
        if exists:
            items = os.listdir(loc)
            print(f'  Contents: {items[:5]}')
            for item in items[:20]:
                full = os.path.join(loc, item)
                if os.path.isdir(full):
                    sub = os.listdir(full)
                    print(f'    {item}/: {len(sub)} items')
    except Exception as e:
        print(f'{loc}: Error - {e}')

# Also check if the zozi project was recently modified or deleted
import time
root = pathlib.Path(r'D:\Projects/10- E-COMMERCE_WEBSITE/zozi')
print(f'\nRoot dir modified: {time.ctime(root.stat().st_mtime)}')

for item in root.iterdir():
    try:
        s = item.stat()
        print(f'  {item.name}: mtime={time.ctime(s.st_mtime)}, size={s.st_size}')
    except:
        pass
