import requests
import sys

pages = [
    "/",
    "/products",
    "/products/1",
    "/suppliers/2",
    "/cart",
    "/checkout",
    "/orders",
    "/profile/referrals",
]

for path in pages:
    try:
        r = requests.get(f"http://localhost:3000{path}", timeout=15)
        content = r.text[:300].lower()
        status = r.status_code
        has_skeleton = "loadingskeleton" in r.text.lower()
        has_error = "error" in content[:200]
        
        print(f"{status:3d} | {path:<30} | skeleton={has_skeleton} | error={has_error}")
    except Exception as e:
        print(f"ERR | {path:<30} | {e}")
