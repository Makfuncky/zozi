import ctypes
from ctypes import wintypes
import os

kernel32 = ctypes.windll.kernel32

def check_and_read(path):
    """Check file attributes, size, and try to read."""
    # Check attributes
    attrs = kernel32.GetFileAttributesW(path, 0)
    if attrs == 0:
        return f'  attrs: 0 (doesn\'t exist)'
    
    # Try to open
    handle = kernel32.CreateFileW(path, 0x80000000, 1, 0, 3, 0, 0)
    if handle == 0 or handle == -1 or handle == 0xFFFFFFFF:
        err = kernel32.GetLastError()
        return f'  attrs: {attrs} (exists), CreateFileW failed (error {err})'
    
    # Get size
    size = kernel32.GetFileSize(handle, 0)
    if size == 0xFFFFFFFF:
        err = kernel32.GetLastError()
        kernel32.CloseHandle(handle)
        return f'  attrs: {attrs}, GetFileSize failed (error {err})'
    
    # Read
    data = ctypes.create_string_buffer(size)
    read = ctypes.c_ulong(0)
    result = kernel32.ReadFile(handle, data, size, ctypes.byref(read), 0)
    kernel32.CloseHandle(handle)
    
    if not result:
        return f'  attrs: {attrs}, size={size}, ReadFile failed'
    
    content = data.raw[:read.value]
    return f'  attrs: {attrs}, size={size}, read={read.value}, content_preview={content[:100]}'

# Test with main.py - this worked before
paths = [
    r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend\main.py',
    r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi\backend\main.py',
    r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi\backend\routers\auth.py',
    r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi\backend\routers\security\auth.py',
    r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi\backend\data\routers_security_auth.py',
    r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi\backend\services\supplier\supplier_countries_service.py',
    r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend\requirements.txt',
    r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\AGENTS.md',
]

for p in paths:
    print(f'{p}:')
    print(check_and_read(p))
    print()
