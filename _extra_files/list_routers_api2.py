import ctypes, os, json, struct, re
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32

# WIN32_FIND_DATA structure (Unicode version)
class WIN32_FIND_DATAW(ctypes.Structure):
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
    data = WIN32_FIND_DATAW()
    handle = kernel32.FindFirstFileW(pattern, ctypes.byref(data))
    
    if handle == 0 or handle == -1 or handle == 0xFFFFFFFF:
        err = kernel32.GetLastError()
        return [], f'FindFirstFileW failed (error {err})'
    
    results = []
    
    if data.cFileName and data.cFileName not in ['.', '..']:
        size = data.nFileSizeLow + (data.nFileSizeHigh << 32)
        is_dir = bool(data.dwFileAttributes & 0x10)
        results.append((data.cFileName, size, is_dir))
    
    while kernel32.FindNextFileW(handle, ctypes.byref(data)):
        if data.cFileName and data.cFileName not in ['.', '..']:
            size = data.nFileSizeLow + (data.nFileSizeHigh << 32)
            is_dir = bool(data.dwFileAttributes & 0x10)
            results.append((data.cFileName, size, is_dir))
    
    kernel32.FindClose(handle)
    return results, None

def read_file(path):
    """Read file using Windows API."""
    handle = kernel32.CreateFileW(path, 0x80000000, 1, 0, 3, 0, 0)
    if handle == 0 or handle == -1 or handle == 0xFFFFFFFF:
        return None, f'CreateFileW failed (error {kernel32.GetLastError()})'
    
    size = kernel32.GetFileSize(handle, 0)
    data = ctypes.create_string_buffer(size)
    read = ctypes.c_ulong(0)
    kernel32.ReadFile(handle, data, size, ctypes.byref(read), 0)
    kernel32.CloseHandle(handle)
    return data.raw[:read.value], None

# List routers directory using Windows API
routers = r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend\routers'
results, err = find_files(r'\\?\D:\Projects/10- E-COMMERCE WEBSITE\zozi\backend\routers\*')

if not results:
    # Try without the \\?\ prefix
    results, err = find_files(r'D:\Projects/10- E-COMMERCE WEBSITE\zozi\backend\routers\*')

if results:
    dirs = sorted([(n, s, d) for n, s, d in results if d], key=lambda x: x[0])
    files = sorted([(n, s, d) for n, s, d in results if not d], key=lambda x: x[0])
    
    print(f'Routers directory contents:')
    print(f'  Directories ({len(dirs)}):')
    for name, size, is_dir in dirs:
        print(f'    {name}/')
    
    print(f'  Files ({len(files)}):')
    for name, size, is_dir in files:
        print(f'    {name} ({size} bytes)')
else:
    print(f'Error: {err}')

# Read main.py
print('\n--- main.py ---')
main_path = r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend\main.py'
content, err = read_file(main_path)
if content:
    text = content.decode('utf-8', errors='replace')
    print(f'Size: {len(content)} bytes')
    
    # Find router_names list
    for match in re.finditer(r'router_names\s*=\s*\[(.*?)\]', text, re.DOTALL):
        names_text = match.group(1)
        names = re.findall(r'"([^"]+)"', names_text)
        print(f'\n{len(names)} routers in router_names:')
        for n in sorted(names):
            print(f'  {n}')
        break
else:
    print(f'Error reading main.py: {err}')

# Check if ws_chat import was fixed
if content:
    text = content.decode('utf-8', errors='replace')
    if 'ws_chat' in text:
        # Find the import line
        for line in text.split('\n'):
            if 'ws_chat' in line:
                print(f'\nws_chat reference: {line.strip()}')

# Check if the security subfolder was deleted (check via API)
print('\n--- Checking security subfolder ---')
sec_results, sec_err = find_files(r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend\routers\security\*')
if sec_results:
    print(f'security/ still has {len(sec_results)} items')
    for name, size, is_dir in sec_results[:10]:
        print(f'  {name} ({size} bytes, dir={is_dir})')
else:
    print(f'security/ deleted or error: {sec_err}')

# Check auth.py content
print('\n--- auth.py content ---')
auth_path = r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend\routers\auth.py'
auth_content, auth_err = read_file(auth_path)
if auth_content:
    auth_text = auth_content.decode('utf-8', errors='replace')
    print(f'Size: {len(auth_content)} bytes')
    print(f'First 300 chars:')
    print(auth_text[:300])
    print(f'\nLast 200 chars:')
    print(auth_text[-200:])
else:
    print(f'Error: {auth_err}')
