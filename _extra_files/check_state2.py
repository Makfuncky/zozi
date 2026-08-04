import subprocess, os, re

base = r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend'

# Use cmd to list files
result = subprocess.run(['cmd', '/c', f'dir "{base}\\routers\\*" /b /a-d 2^>nul'], capture_output=True, text=True)
print("CMD listing routers/*.py:")
files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
print(f"Found {len(files)} .py files")
for f in sorted(files)[:20]:
    print(f"  {f}")
if len(files) > 20:
    print(f"  ... and {len(files) - 20} more")

# List directories
result2 = subprocess.run(['cmd', '/c', f'dir "{base}\\routers\\*" /ad /b 2^>nul'], capture_output=True, text=True)
print(f"\nCMD listing routers/ dirs:")
dirs = [d.strip() for d in result2.stdout.strip().split('\n') if d.strip()]
print(f"Found {len(dirs)} subdirectories")
for d in sorted(dirs):
    print(f"  {d}")

# List backend directory
result3 = subprocess.run(['cmd', '/c', f'dir "{base}" /b /a 2^>nul'], capture_output=True, text=True)
print(f"\nCMD listing backend/:")
items = [i.strip() for i in result3.stdout.strip().split('\n') if i.strip()]
for item in sorted(items):
    print(f"  {item}")

# Check security subfolder
result4 = subprocess.run(['cmd', '/c', f'dir "{base}\\routers\\security\\" /b /a-d 2^>nul'], capture_output=True, text=True)
print(f"\nsecurity/ contents:")
sec_files = [f.strip() for f in result4.stdout.strip().split('\n') if f.strip()]
print(f"Found {len(sec_files)} files")
for f in sec_files[:10]:
    print(f"  {f}")

# Check auth.py
result5 = subprocess.run(['cmd', '/c', f'dir "{base}\\routers\\auth.py" /b /s 2^>nul'], capture_output=True, text=True)
print(f"\nauth.py check: {result5.stdout.strip()}")
