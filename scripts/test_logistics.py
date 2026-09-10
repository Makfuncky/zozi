import asyncio
import json
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8000"
LOGIN_EMAIL = "logistics@zozi.com"
LOGIN_PASSWORD = "T3st_Log!stics_Secure#2024"

ENDPOINTS = [
    ("GET", "/logistics-partner/dashboard", "dashboard"),
    ("GET", "/api/v1/logistics/shipments", "shipments"),
    ("GET", "/api/v1/logistics/accounts/profile", "profile"),
    ("GET", "/api/v1/logistics/analytics", "analytics"),
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        # Login
        print("=== LOGIN ===")
        login_api = await context.request.post(
            f"{BASE_URL}/api/v1/auth/login",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD})
        )
        login_status = login_api.status
        login_body = await login_api.text()
        print(f"Login status: {login_status}")
        print(f"Login response: {login_body[:500]}")
        
        token = None
        try:
            login_json = json.loads(login_body)
            token = login_json.get("access_token") or login_json.get("token")
        except:
            pass
        
        if not token:
            print("FAILED to obtain token")
            await browser.close()
            return
        
        print(f"Token obtained: {token[:20]}...")
        
        # Test endpoints
        print("\n=== ENDPOINT TESTS ===")
        results = []
        for method, path, name in ENDPOINTS:
            url = f"{BASE_URL}{path}"
            resp = await context.request.get(
                url,
                headers={"Authorization": f"Bearer {token}"}
            )
            status = resp.status
            body = await resp.text()
            
            # Try to parse JSON
            has_data = False
            try:
                json_body = json.loads(body)
                if isinstance(json_body, dict):
                    has_data = len(json_body) > 0
                elif isinstance(json_body, list):
                    has_data = len(json_body) > 0
                else:
                    has_data = bool(json_body)
                body_preview = json.dumps(json_body, indent=2)[:400]
            except:
                has_data = len(body) > 10
                body_preview = body[:400]
            
            result = "PASS" if status == 200 and has_data else "FAIL"
            results.append((name, status, has_data, result))
            print(f"\n--- {name}: {method} {path} ---")
            print(f"  Status: {status}")
            print(f"  Has data: {has_data}")
            print(f"  Result: {result}")
            print(f"  Preview: {body_preview}")
        
        # Summary
        print("\n=== SUMMARY ===")
        for name, status, has_data, result in results:
            print(f"  {name}: HTTP {status} | data={has_data} | {result}")
        
        await browser.close()

asyncio.run(main())
