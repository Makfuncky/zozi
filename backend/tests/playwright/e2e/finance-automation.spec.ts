import { expect, test } from "@playwright/test";
import { apiLogin } from "../helpers/auth";

const BASE = "http://127.0.0.1:8000";

test.describe("Finance Automation Suite", () => {
  let token: string;

  test.beforeAll(async ({ page }) => {
    token = await apiLogin(page, "admin@zozi.com", "admin123");
  });

  test.describe("1. Gateway Reconciliation", () => {
    test("run 3-way gateway reconciliation", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/gateway-reconciliation/run`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
      const data = await resp.json();
      expect(data).toHaveProperty("processed");
      expect(data).toHaveProperty("reconciled");
      expect(data).toHaveProperty("exceptions");
    });

    test("match a specific gateway settlement", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/gateway-reconciliation/match/1`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
    });

    test("reconcile COD deposit for an order", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/cod-reconcile/1`,
        {
          headers: { Authorization: `Bearer ${token}` },
          json: { deposited_amount: "100.00" },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
    });
  });

  test.describe("2. Payout Batches", () => {
    test("generate supplier payout batches", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/payout-batches/generate`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
      const data = await resp.json();
      expect(data).toHaveProperty("batches_created");
    });

    test("generate logistics payout batches", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/payout-batches/logistics`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
    });

    test("supplier approve batch", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/payout-batches/1/approve`,
        {
          headers: { Authorization: `Bearer ${token}` },
          json: { supplier_id: 1, approved: true },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
    });
  });

  test.describe("3. Refund Posting", () => {
    test("post refund journal entries", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/refunds/1/post`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
    });
  });

  test.describe("4. Credit Control", () => {
    test("check customer credit", async ({ page }) => {
      const resp = await page.request.get(
        `${BASE}/automation/credit-check/1`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
      const data = await resp.json();
      expect(data).toHaveProperty("approved");
      expect(data).toHaveProperty("credit_hold");
    });

    test("enforce auto credit holds", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/credit-control/enforce`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
      const data = await resp.json();
      expect(data).toHaveProperty("holds_placed");
      expect(data).toHaveProperty("holds_released");
    });

    test("get customer credit summary", async ({ page }) => {
      const resp = await page.request.get(
        `${BASE}/automation/credit-summary/1`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
      const data = await resp.json();
      expect(data).toHaveProperty("customer_name");
      expect(data).toHaveProperty("credit_limit");
      expect(data).toHaveProperty("outstanding_ar");
    });
  });

  test.describe("5. Core Automation", () => {
    test("run full automation suite", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/run`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
      const data = await resp.json();
      expect(data).toHaveProperty("daily_finance");
      expect(data).toHaveProperty("cash_snapshot");
      expect(data).toHaveProperty("vat");
      expect(data).toHaveProperty("alerts");
      expect(data).toHaveProperty("gateway_reconciliation");
      expect(data).toHaveProperty("supplier_payouts");
      expect(data).toHaveProperty("logistics_payouts");
      expect(data).toHaveProperty("credit_control");
      expect(data).toHaveProperty("fx_revaluation");
      expect(data).toHaveProperty("three_way_match");
      expect(data).toHaveProperty("dunning");
      expect(data).toHaveProperty("ecommerce_invoice");
      expect(data).toHaveProperty("cod_reconciliation");
      expect(data).toHaveProperty("ai_bank_reconciliation");
      expect(data).toHaveProperty("email_inbox");
      expect(data).toHaveProperty("ai_categorization");
      expect(data).toHaveProperty("period_close");
    });

    test("take cash position snapshot", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/cash-snapshot`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
    });

    test("compute VAT remittance", async ({ page }) => {
      const now = new Date();
      const year = now.getFullYear();
      const month = now.getMonth() + 1;
      const resp = await page.request.post(
        `${BASE}/automation/vat?period_year=${year}&period_month=${month}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
    });

    test("run alert engine", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/alerts`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
      const data = await resp.json();
      expect(Array.isArray(data)).toBe(true);
    });
  });

  test.describe("6. AI Automation Engines", () => {
    test("AI fuzzy bank reconciliation", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/ai/bank-reconciliation`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
      const data = await resp.json();
      expect(data).toHaveProperty("processed");
      expect(data).toHaveProperty("matched");
      expect(data).toHaveProperty("exceptions");
    });

    test("process email inbox for invoices", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/email/inbox`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
      const data = await resp.json();
      expect(data).toHaveProperty("scanned");
    });

    test("process single invoice email", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/email/process`,
        {
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
          json: { email_text: "AWS invoice $150.00 for server costs", sender: "aws@amazon.com" },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
      const data = await resp.json();
      expect(data).toHaveProperty("status");
    });

    test("batch AI categorize expenses", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/ai/categorize/batch`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
      const data = await resp.json();
      expect(data).toHaveProperty("processed");
      expect(data).toHaveProperty("categorized");
    });

    test("mobile scan endpoint info", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/mobile/scan`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
      const data = await resp.json();
      expect(data).toHaveProperty("endpoint");
      expect(data).toHaveProperty("method");
    });
  });

  test.describe("6. Payout Batches - Supplier Flow", () => {
    test("pending batches for supplier", async ({ page }) => {
      const resp = await page.request.get(
        `${BASE}/automation/payout-batches/pending/1`,
        {
          headers: { Authorization: `Bearer ${token}` },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
      const data = await resp.json();
      expect(Array.isArray(data)).toBe(true);
    });
  });

  test.describe("7. Gateway Settlement Detail", () => {
    test("match gateway settlement by ID", async ({ page }) => {
      const resp = await page.request.post(
        `${BASE}/automation/gateway-reconciliation/match/1`,
        {
          headers: { Authorization: `Bearer ${token}` },
          json: { bank_statement_line_id: 1 },
          failOnStatusCode: false,
        }
      );
      expect(resp.status()).toBe(200);
      const data = await resp.json();
      expect(data).toHaveProperty("status");
    });
  });
});