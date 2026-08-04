import os
print(f"GIT_DIR: {os.environ.get('GIT_DIR', 'not set')}")
print(f"GIT_WORK_TREE: {os.environ.get('GIT_WORK_TREE', 'not set')}")
for k, v in os.environ.items():
    if 'GIT' in k.upper():
        print(f"  {k}={v}")
