"""Playwright smoke test for the VAT remittance fix.

Uses Playwright's request API to:
1. POST /auth/login directly on the backend (localhost:8000)
2. POST /automation/run with the received Bearer token
3. Assert the response has a valid 'vat' payload

Run: python e2e/test_vat_remittance_fix.py
"""
from __future__ import annotations

import json
import sys
from datetime import date

from playwright.sync_api import sync_playwright

BACKEND = "http://localhost:8000"
AUTH_PATH = "/auth/login"
AUTOMATION_PATH = "/automation/run"
ADMIN_CREDS = {"username": "admin@zozi.com", "password": "admin123"}


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            base_url=BACKEND,
            viewport={"width": 1440, "height": 900},
        )
        page = context.new_page()

        # ── 1. Admin login directly against backend ────────────────────────
        login_resp = page.request.post(
            f"{BACKEND}{AUTH_PATH}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(ADMIN_CREDS),
            fail_on_status_code=False,
        )
        print(f"[auth] login status={login_resp.status} ok={login_resp.ok}")

        if not login_resp.ok:
            print(f"[auth] login failed: {login_resp.text()[:500]}")
            context.close()
            browser.close()
            return 1

        try:
            login_body = login_resp.json()
        except Exception:
            print(f"[auth] login response not JSON: {login_resp.text()[:500]}")
            context.close()
            browser.close()
            return 1

        access_token = login_body.get("access_token")
        if not access_token:
            print(f"[auth] login response missing access_token: {json.dumps(login_body)[:500]}")
            context.close()
            browser.close()
            return 1

        print(f"[auth] obtained access_token ({len(access_token)} chars)")

        # ── 2. Call the automation endpoint with Bearer token ──────────────
        today = date.today()
        payload = json.dumps({
            "country_code": None,
            "period_year": today.year,
            "period_month": today.month,
        })

        automation_resp = page.request.post(
            f"{BACKEND}{AUTOMATION_PATH}",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
            data=payload,
            fail_on_status_code=False,
        )

        print(f"[automation] status={automation_resp.status} ok={automation_resp.ok}")

        try:
            body = automation_resp.json()
        except Exception:
            body = {"raw": automation_resp.text()}

        if not automation_resp.ok:
            print(f"[automation] error body: {json.dumps(body, indent=2)[:3000]}")
            context.close()
            browser.close()
            return 1

        # ── 3. Assertions ──────────────────────────────────────────────────
        print(f"[automation] response keys: {sorted(body.keys())}")

        if "vat" not in body:
            print("FAIL: response missing 'vat' key")
            print(json.dumps(body, indent=2)[:3000])
            context.close()
            browser.close()
            return 1

        vat = body["vat"]
        required = {"period", "vat_collected", "vat_paid", "net_due"}
        missing = required - vat.keys()
        if missing:
            print(f"FAIL: 'vat' payload missing keys: {missing}")
            print(json.dumps(vat, indent=2))
            context.close()
            browser.close()
            return 1

        print(f"[vat] period={vat['period']} collected={vat['vat_collected']} "
              f"paid={vat['vat_paid']} net_due={vat['net_due']}")
        print("PASS: VAT remittance endpoint returned a valid payload")

        context.close()
        browser.close()
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}")
        sys.exit(1)
