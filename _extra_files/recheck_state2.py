import os, sys, time, ctypes
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32
kernel32.GetFileAttributesW.restype = wintypes.DWORD
INVALID = 0xFFFFFFFF

# The key insight: D:\Projects/10- WORKS but D:\Projects\10- DOESN'T
# Let's try different approaches

# 1. Try from the root with GetFullPathName
def get_full_path(rel_path, base):
    # Use GetFullPathName to resolve the path
    buf = ctypes.create_unicode_buffer(32768)
    result = kernel32.GetFullPathNameW(rel_path, 32768, buf, None)
    return buf.value if result else None

# 2. Try os.chdir + relative path
print('=== Method 1: chdir + relative path ===')
try:
    os.chdir(r'D:\Projects/10- E-COMMERCE WEBSITE\zozi')
    print(f'CWD: {os.getcwd()}')
    
    # Check if main.py exists
    for path in ['backend/main.py', 'backend/routers/auth.py', 'AGENTS.md']:
        exists = os.path.exists(path)
        try:
            size = os.path.getsize(path)
            print(f'  {path}: exists={exists}, size={size}')
        except:
            print(f'  {path}: exists={exists}, size=N/A')
except Exception as e:
    print(f'Error: {e}')

print()
print('=== Method 2: Windows API with chdir ===')
os.chdir(r'D:\Projects/10- E-COMMERCE WEBSITE\zozi')

paths_to_check = [
    r'backend\main.py',
    r'backend\routers\auth.py',
    r'backend\routers\security\auth.py',
    r'AGENTS.md',
    r'backend\requirements.txt',
]

for p in paths_to_check:
    attrs = kernel32.GetFileAttributesW(p)
    exists = attrs != INVALID and attrs != 0
    print(f'  {p}: attrs={attrs}, exists={exists}')
    
    if exists:
        handle = kernel32.CreateFileW(p, 0x80000000, 1, 0, 3, 0, 0)
        if handle != 0 and handle != -1 and handle != 0xFFFFFFFF:
            size = kernel32.GetFileSize(handle, 0)
            data = ctypes.create_string_buffer(min(size, 500))
            read = ctypes.c_ulong(0)
            kernel32.ReadFile(handle, data, min(size, 500), ctypes.byref(read), 0)
            kernel32.CloseHandle(handle)
            text = data.raw[:read.value].decode('utf-8', errors='replace')
            print(f'    size={size}, preview: {text[:100]}')
        else:
            err = kernel32.GetLastError()
            print(f'    CreateFileW failed: {err}')

print()
print('=== Method 3: PowerShell listing ===')
import subprocess
result = subprocess.run(['powershell', '-Command', 
    'Get-ChildItem -Path "backend" -File -Recurse | Select-Object -First 20 | Format-Table FullName, Length'],
    capture_output=True, text=True)
print(result.stdout[:2000])
if result.stderr:
    print(f'STDERR: {result.stderr[:500]}')
