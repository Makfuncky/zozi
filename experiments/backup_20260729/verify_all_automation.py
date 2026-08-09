import urllib.request, json, sys

BASE = "http://127.0.0.1:8000"

def login():
    data = json.dumps({"email": "admin@zozi.com", "password": "admin123"}).encode()
    req = urllib.request.Request(f"{BASE}/auth/login", data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=5)
    return json.loads(resp.read())["access_token"]

def call(method, path, body=None, token=None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, method=method, headers=headers, data=data)
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return 0, {"error": str(e)}

def main():
    token = login()
    print(f"Logged in as admin, token: {token[:20]}...")
    print()

    test_groups = {
        "1. Core Automation": [
            ("POST", "/automation/run", None),
            ("POST", "/automation/cash-snapshot", None),
            ("POST", "/automation/vat?period_year=2026&period_month=7", None),
            ("POST", "/automation/reports", None),
            ("POST", "/automation/alerts", None),
        ],
        "2. Gateway Reconciliation": [
            ("POST", "/automation/gateway-reconciliation/run", None),
            ("POST", "/automation/gateway-reconciliation/match/1", None),
            ("POST", "/automation/cod-reconcile/1", {"deposited_amount": "100.00"}),
        ],
        "3. Payout Batches": [
            ("POST", "/automation/payout-batches/generate", None),
            ("POST", "/automation/payout-batches/logistics", None),
            ("GET", "/automation/payout-batches/pending/1", None),
            ("POST", "/automation/payout-batches/1/approve", {"supplier_id": 1, "approved": True}),
        ],
        "4. Refund Posting": [
            ("POST", "/automation/refunds/1/post", None),
        ],
        "5. Credit Control": [
            ("GET", "/automation/credit-check/1", None),
            ("POST", "/automation/credit-control/enforce", None),
            ("GET", "/automation/credit-summary/1", None),
        ],
        "6. AI Automation": [
            ("POST", "/automation/ai/bank-reconciliation", None),
            ("POST", "/automation/email/inbox", None),
            ("POST", "/automation/email/process", {"email_text": "AWS invoice $150.00 for server costs", "sender": "aws@amazon.com"}),
            ("POST", "/automation/ai/categorize/batch", None),
            ("POST", "/automation/mobile/scan", None),
        ],
    }

    total = 0
    passed = 0
    failed = 0

    for group_name, tests in test_groups.items():
        print(f"--- {group_name} ---")
        for method, path, body in tests:
            total += 1
            status, result = call(method, path, body, token)
            if status == 200:
                passed += 1
                print(f"  OK: {method} {path} -> {status}")
            else:
                failed += 1
                error_msg = result.get("error", str(result))[:100]
                print(f"  FAIL: {method} {path} -> {status}: {error_msg}")
        print()

    print(f"RESULTS: {passed}/{total} passed, {failed}/{total} failed")
    if failed == 0:
        print("ALL AUTOMATION ENDPOINTS WORKING!")
    else:
        print("Some endpoints need attention.")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())