import ctypes, json
import pathlib

kernel32 = ctypes.windll.kernel32

def read_file_winapi(path, max_size=10*1024*1024):
    """Read file using Windows API."""
    handle = kernel32.CreateFileW(
        path,
        0x80000000,  # GENERIC_READ
        1,  # FILE_SHARE_READ
        0,  # LPSECURITY_ATTRIBUTES
        3,  # OPEN_EXISTING
        0,  # dwFlagsAndAttributes
        0   # hTemplateFile
    )
    if handle == -1 or handle == 0xFFFFFFFF:
        err = ctypes.windll.kernel32.GetLastError()
        return None, f'CreateFileW failed (error {err})'
    
    # Get file size
    size = kernel32.GetFileSize(handle, 0)
    if size > max_size:
        size = max_size
    
    data = ctypes.create_string_buffer(size)
    read = ctypes.c_ulong(0)
    result = kernel32.ReadFile(handle, data, size, ctypes.byref(read), 0)
    kernel32.CloseHandle(handle)
    
    if not result:
        err = ctypes.windll.kernel32.GetLastError()
        return None, f'ReadFile failed (error {err})'
    
    return data.raw[:read.value], None

# Read main.py using the exact path that worked
path = r'D:\Projects/10- E-COMMERCE WEBSITE\zozi\backend\main.py'
content, error = read_file_winapi(path)

if content:
    print(f'Successfully read {path}')
    print(f'Size: {len(content)} bytes')
    decoded = content.decode('utf-8', errors='replace')
    print(f'First 500 chars:')
    print(decoded[:500])
    
    # Save it to a temp file for inspection
    pathlib.Path(r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi/recovered_main.py').write_bytes(content)
    print('Saved to recovered_main.py')
else:
    print(f'Failed to read: {error}')

# Also try reading router files
for router_dir in [
    r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend\routers',
    r'D:\Projects\10- E-COMMERCE_WEBSITE/zozi/backend/routers',
]:
    exists = kernel32.GetFileAttributesW(router_dir, 0) != 0
    print(f'\n{router_dir} exists via WinAPI: {exists}')

# List the routers directory
handle = kernel32.FindFirstFileW(r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend\routers\*', None)
