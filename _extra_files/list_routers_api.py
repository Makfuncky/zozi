import ctypes, os, json, struct
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32
kernel32.FindFirstFileW.restype = wintypes.HANDLE
kernel32.FindNextFileW.argtypes = [wintypes.HANDLE, wintypes.LPVOID]
kernel32.FindNextFileW.restype = wintypes.BOOL

# WIN32_FIND_DATA structure
class WIN32_FIND_DATA(ctypes.Structure):
    _fields_ = [
        ('dwFileAttributes', wintypes.DWORD),
        ('ftCreationTime', wintypes.FILETIME),
        ('ftLastAccessTime', wintypes.FILETIME),
        ('ftLastWriteTime', wintypes.FILETIME),
        ('nFileSizeHigh', wintypes.DWORD),
        ('nFileSizeLow', wintypes.DWORD),
        ('dwReserved0', wintypes.DWORD),
        ('dwReserved1', wintypes.DWORD),
        ('cFileName', wintypes.WCHAR * 260),
        ('cAlternateFileName', wintypes.WCHAR * 14),
    ]

def find_files(pattern):
    """Find files matching pattern using Windows API."""
    handle = kernel32.FindFirstFileW(pattern, ctypes.byref(WIN32_FIND_DATA()))
    if handle == -1 or handle == 0xFFFFFFFF:
        err = kernel32.GetLastError()
        return [], f'FindFirstFileW failed (error {err})'
    
    results = []
    data = WIN32_FIND_DATA()
    
    # Get first file
    ctypes.memmove(ctypes.byref(data), ctypes.byref(data), ctypes.sizeof(data))
    
    # FindFirstFile already populated data, so let's use a different approach
    data = WIN32_FIND_DATA()
    kernel32.FindClose(handle)
    
    # Use a simpler approach - call FindFirstFileW and then FindNextFileW
    data = WIN32_FIND_DATA()
    handle = kernel32.FindFirstFileW(pattern, ctypes.byref(data))
    
    if handle == -1 or handle == 0xFFFFFFFF:
        return [], f'FindFirstFileW failed'
    
    if data.cFileName:
        is_dir = bool(data.dwFileAttributes & 0x10)  # FILE_ATTRIBUTE_DIRECTORY
        results.append((data.cFileName, data.nFileSizeLow + (data.nFileSizeHigh << 32), is_dir))
    
    while kernel32.FindNextFileW(handle, ctypes.byref(data)):
        if data.cFileName:
            is_dir = bool(data.dwFileAttributes & 0x10)
            results.append((data.cFileName, data.nFileSizeLow + (data.nFileSizeHigh << 32), is_dir))
    
    kernel32.FindClose(handle)
    return results, None

# List routers directory using Windows API
routers = r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend\routers'
results, err = find_files(routers + r'\*')

if results:
    dirs = sorted([(n, s, d) for n, s, d in results if d], key=lambda x: x[0])
    files = sorted([(n, s, d) for n, s, d in results if not d], key=lambda x: x[0])
    
    print(f'Routers directory contents:')
    print(f'  Directories ({len(dirs)}):')
    for name, size, is_dir in dirs:
        if name not in ['.', '..']:
            print(f'    {name}/')
    
    print(f'  Files ({len(files)}):')
    for name, size, is_dir in files:
        print(f'    {name} ({size} bytes)')
else:
    print(f'Error: {err}')

# Also check what main.py imports
print('\n--- Checking main.py router imports ---')
main_path = r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend\main.py'
handle = kernel32.CreateFileW(main_path, 0x80000000, 1, 0, 3, 0, 0)
if handle != -1 and handle != 0xFFFFFFFF:
    size = kernel32.GetFileSize(handle, 0)
    data = ctypes.create_string_buffer(size)
    read = ctypes.c_ulong(0)
    kernel32.ReadFile(handle, data, size, ctypes.byref(read), 0)
    kernel32.CloseHandle(handle)
    content = data.raw[:read.value].decode('utf-8', errors='replace')
    
    # Find router_names
    import re
    for match in re.finditer(r"router_names\s*=\s*\[(.*?)\]", content, re.DOTALL):
        print(f'router_names definition found')
        # Extract names
        names_text = match.group(1)
        names = re.findall(r'"([^"]+)"', names_text)
        print(f'{len(names)} routers defined:')
        for n in sorted(names):
            print(f'  {n}')
        break
else:
    print('Could not open main.py')
