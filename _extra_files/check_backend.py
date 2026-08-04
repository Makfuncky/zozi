import os
backend = r'D:\Projects\10- E-COMMERCE_WEBSITE\zozi\backend'
print(f'backend exists: {os.path.exists(backend)}')
print(f'main.py exists: {os.path.exists(os.path.join(backend, "main.py"))}')
print(f'Contents of backend:')
for item in sorted(os.listdir(backend)):
    print(f'  {item}')
