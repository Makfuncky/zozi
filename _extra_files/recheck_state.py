import ctypes, time
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32
kernel32.GetFileAttributesW.restype = wintypes.DWORD
INVALID = 0xFFFFFFFF

def check(path):
    attrs = kernel32.GetFileAttributesW(path)
    exists = attrs != INVALID and attrs != 0
    err = kernel32.GetLastError() if attrs == INVALID else 0
    return attrs, exists, err

paths = [
    r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend\main.py',
    r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi\AGENTS.md',
    r'D:\Projects/10- E-COMMERCE WEBSITE\zozi\AGENTS.md',
]

for path in paths:
    for i in range(3):
        attrs, exists, err = check(path)
        print(f'{path} (attempt {i+1}): attrs={attrs}, exists={exists}, err={err}')
        time.sleep(0.1)
    print()

# Also try reading main.py directly
for path in [paths[0]]:
    handle = kernel32.CreateFileW(path, 0x80000000, 1, 0, 3, 0, 0)
    if handle != 0 and handle != -1 and handle != 0xFFFFFFFF:
        size = kernel32.GetFileSize(handle, 0)
        print(f'Read via CreateFileW: handle={handle}, size={size}')
        kernel32.CloseHandle(handle)
    else:
        err = kernel32.GetLastError()
        print(f'CreateFileW failed: error={err}')
