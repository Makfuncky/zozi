import os, time

rec_bin = r'D:\$Recycle.Bin\S-1-5-21-1339371623-4152739331-235715422-1002'

items = os.listdir(rec_bin)
info_files = [f for f in items if f.startswith('$I')]
rec_files = [f for f in items if f.startswith('$R')]

print(f'Info ($I) files: {len(info_files)}')
print(f'Recycled ($R) files/dirs: {len(rec_files)}')

# Read the info files to find original names
print('\n$Info files (with original names from $I content):')
for f in sorted(info_files):
    full = os.path.join(rec_bin, f)
    try:
        with open(full, 'rb') as fh:
            data = fh.read(500)
        # $I file format: first 4 bytes = size, then filename, etc.
        # Actually, the format is: 4 bytes (unknown), 4 bytes (unknown), 
        # 24 bytes (unknown), 4 bytes (unknown), 48 bytes (filename as UTF-16LE), etc.
        try:
            # Try to extract the original filename from the binary data
            text = data.decode('utf-16-le', errors='replace')
            # Find filename - usually starts after some header bytes
            clean = text.replace('\x00', '').strip()
            if clean:
                print(f'  {f} -> {clean[:100]}')
        except:
            pass
    except Exception as e:
        pass

# List $R files (actual recycled content)
print(f'\n$Recycled ($R) items:')
for f in sorted(rec_files):
    full = os.path.join(rec_bin, f)
    try:
        is_dir = os.path.isdir(full)
        s = os.stat(full)
        size_mb = s.st_size / (1024*1024)
        mtime = time.ctime(s.st_mtime)
        print(f'  {f}: size={size_mb:.2f}MB, mtime={mtime}, is_dir={is_dir}')
        if is_dir:
            # List contents
            contents = os.listdir(full)
            print(f'    Contents ({len(contents)} items): {contents[:5]}...')
        elif size_mb > 0.01:
            print(f'    (first 200 bytes: {open(full, "rb").read(200)})')
    except Exception as e:
        print(f'  {f}: ERROR {e}')
