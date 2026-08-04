import os, os.path
print("os.path.exists:", os.path.exists(".git"))
print("os.path.isdir:", os.path.isdir(".git"))
print("os.path.isfile:", os.path.isfile(".git"))
try:
    items = os.listdir(".git")
    print(f"os.listdir: {len(items)} items")
    print(f"first 5: {items[:5]}")
except Exception as e:
    print(f"os.listdir error: {e}")
