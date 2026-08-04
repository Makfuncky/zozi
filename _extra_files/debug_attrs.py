import ctypes
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32

# Set return type to DWORD (unsigned)
kernel32.GetFileAttributesW.restype = wintypes.DWORD

INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF

def check_file(path):
    attrs = kernel32.GetFileAttributesW(path)
    exists = attrs != INVALID_FILE_ATTRIBUTES and attrs != 0
    
    # Try CreateFileW
    handle = kernel32.CreateFileW(path, 0x80000000, 1, 0, 3, 0, 0)
    can_open = handle != 0 and handle != -1 and handle != 0xFFFFFFFF
    
    if can_open:
        kernel32.CloseHandle(handle)
    
    return attrs, exists, can_open

paths = [
    r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend\main.py',
    r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi\backend\main.py',
    r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi\backend\routers\auth.py',
    r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi\backend\requirements.txt',
    r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\AGENTS.md',
    r'D:\Projects/10- E-COMMERCE WEBSITE\zozi\AGENTS.md',
    r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi\backend',
    r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend',
    r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi',
]

for p in paths:
    attrs, exists, can_open = check_file(p)
    print(f'{p}:')
    print(f'  attrs={attrs} (0x{attrs:08x}), exists={exists}, can_open={can_open}')
    
    # Also try GetLastError
    if attrs == INVALID_FILE_ATTRIBUTES:
        err = kernel32.GetLastError()
        print(f'  LastError: {err}')
    print()
