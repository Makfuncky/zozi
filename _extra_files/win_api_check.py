import ctypes
import os

# Use Windows API directly to check file existence
kernel32 = ctypes.windll.kernel32

def file_exists_wide(path):
    """Check file existence using Windows API."""
    attrs = kernel32.GetFileAttributesW(str(path), 0)
    if attrs == 0:
        err = ctypes.windll.kernel32.GetLastError()
        return False, f'GetFileAttributesW failed (error {err})'
    return True, attrs

def read_file_wide(path, size=100):
    """Read file using Windows API."""
    handle = kernel32.CreateFileW(
        str(path),
        0x80000000,  # GENERIC_READ
        1,  # FILE_SHARE_READ
        0,  # LPSECURITY_ATTRIBUTES
        3,  # OPEN_EXISTING
        0,  # dwFlagsAndAttributes
        0   # hTemplateFile
    )
    if handle == -1 or handle == 0xFFFFFFFF:
        err = ctypes.windll.kernel32.GetLastError()
        return False, f'CreateFileW failed (error {err})'
    
    data = ctypes.create_string_buffer(size)
    read = ctypes.c_ulong(0)
    result = kernel32.ReadFile(handle, data, size, ctypes.byref(read), 0)
    kernel32.CloseHandle(handle)
    
    if not result:
        err = ctypes.windll.kernel32.GetLastError()
        return False, f'ReadFile failed (error {err})'
    
    return True, data.raw[:read.value]

# Try multiple paths for main.py
paths_to_try = [
    r'D:\Projects/10- E-COMMERCE WEBSITE\zozi\backend\main.py',
    r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi\backend\main.py',
    r'D:/Projects/10- E-COMMERCE_WEBSITE/zozi/backend/main.py',
    r'backend\main.py',
    r'backend/main.py',
]

os.chdir(r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi')

for p in paths_to_try:
    exists, info = file_exists_wide(p)
    if exists:
        size = os.path.getsize(p)
        print(f'EXISTS: {p} (size={size})')
        success, content = read_file_wide(p, 100)
        if success:
            print(f'  First 100 bytes: {content[:100]}')
        else:
            print(f'  Read error: {content}')
    else:
        print(f'NOT FOUND: {p} ({info})')

# Also try listing the directory using FindFirstFile
print('\nListing backend directory using Windows API:')
import glob
for pattern in [
    r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend\*',
    r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi\backend\*.py',
]:
    matches = glob.glob(pattern)
    print(f'  glob({pattern}): {matches[:10]}')
    if len(matches) > 10:
        print(f'    ... and {len(matches) - 10} more')
