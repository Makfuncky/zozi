"""
Read all backend files via Windows API and save to a temp location,
then copy them back so they can be accessed normally.
"""
import ctypes
from ctypes import wintypes
import os, pathlib

kernel32 = ctypes.windll.kernel32

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

def read_file_api(path):
    handle = kernel32.CreateFileW(path, 0x80000000, 1, 0, 3, 0, 0)
    if handle == 0 or handle == -1 or handle == 0xFFFFFFFF:
        return None, f'Cannot open: {path}'
    size = kernel32.GetFileSize(handle, 0)
    data = ctypes.create_string_buffer(size)
    read = ctypes.c_ulong(0)
    kernel32.ReadFile(handle, data, size, ctypes.byref(read), 0)
    kernel32.CloseHandle(handle)
    return data.raw[:read.value], None

def file_exists(path):
    return kernel32.GetFileAttributesW(path, 0) != 0

def find_first(pattern):
    data = WIN32_FIND_DATAW()
    handle = kernel32.FindFirstFileW(pattern, ctypes.byref(data))
    if handle == 0 or handle == -1 or handle == 0xFFFFFFFF:
        return None, kernel32.GetLastError()
    return handle, data

def find_next(handle, data):
    return kernel32.FindNextFileW(handle, ctypes.byref(data))

def list_dir_recursive(path):
    """List all files in a directory recursively using Windows API."""
    all_files = []
    
    def _walk(dir_path):
        handle, data = find_first(dir_path + '\\*')
        if handle is None:
            return
        
        try:
            while True:
                name = data.cFileName
                if name and name not in ['.', '..']:
                    full = dir_path + '\\' + name
                    is_dir = bool(data.dwFileAttributes & 0x10)
                    if is_dir:
                        _walk(full)
                    else:
                        size = data.nFileSizeLow + (data.nFileSizeHigh << 32)
                        all_files.append((full, size))
                
                data = WIN32_FIND_DATAW()
                if not find_next(handle, data):
                    break
        finally:
            kernel32.FindClose(handle)
    
    _walk(path)
    return all_files

# List all backend files
backend = r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend'
print(f'Scanning {backend}...')
files = list_dir_recursive(backend)
print(f'Found {len(files)} files')

# Categorize
py_files = [(p, s) for p, s in files if p.endswith('.py')]
other_files = [(p, s) for p, s in files if not p.endswith('.py')]
print(f'  .py files: {len(py_files)}')
print(f'  Other files: {len(other_files)}')

# Check for routers directory
routers_path = backend + r'\routers'
if file_exists(routers_path):
    print(f'\nRouters directory exists')
    router_files = list_dir_recursive(routers_path)
    print(f'  {len(router_files)} files in routers/')
    
    dirs = set()
    flat_files = []
    for p, s in router_files:
        parts = p.split('\\')
        # Check if it's in a subdirectory
        rel = p[len(routers_path)+1:]
        if '\\' in rel:
            sub = rel.split('\\')[0]
            dirs.add(sub)
        else:
            flat_files.append(os.path.basename(p))
    
    print(f'  Subdirectories: {sorted(dirs)}')
    print(f'  Flat files: {len(flat_files)}')
    print(f'  Sample flat files: {sorted(flat_files)[:20]}')

# Check if auth.py has full implementation or is a shim
auth_path = backend + r'\routers\auth.py'
if file_exists(auth_path):
    content, err = read_file_api(auth_path)
    if content:
        text = content.decode('utf-8', errors='replace')
        # Check if it's a re-export shim or full implementation
        if 'from data.routers_security_auth import' in text:
            print('\nauth.py: SHIM (imports from data.routers_security_auth)')
            print(f'  Size: {len(content)} bytes')
        elif 'APIRouter' in text and 'router = APIRouter' in text:
            print('\nauth.py: FULL IMPLEMENTATION (contains APIRouter)')
            print(f'  Size: {len(content)} bytes')
            print(f'  First 500 chars:')
            print(text[:500])
        else:
            print(f'\nauth.py: UNKNOWN type, size={len(content)}')
            print(text[:500])

# Check security/auth.py (the original subfolder file)
sec_auth_path = backend + r'\routers\security\auth.py'
if file_exists(sec_auth_path):
    content, err = read_file_api(sec_auth_path)
    if content:
        text = content.decode('utf-8', errors='replace')
        print(f'\nsecurity/auth.py: EXISTS, size={len(content)}')
        print(text[:500])
