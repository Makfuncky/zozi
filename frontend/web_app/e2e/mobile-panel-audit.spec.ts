import fs from "node:fs";
import path from "node:path";
import { expect, test, devices, type Page, type TestInfo } from "@playwright/test";

test.describe.configure({ timeout: 180_000 });
test.use({ browserName: "chromium", ...devices["iPhone 13"] });

type LoginConfig = {
  username: string;
  password: string;
  landingRoute: string;
  expectedUrl: RegExp;
};

type RouteAudit = {
  label: string;
  route: string;
  login: LoginConfig;
};

type OverflowReport = {
  route: string;
  viewport: number;
  scrollWidth: number;
  hasOverflow: boolean;
  offenders: Array<{
    tag: string;
    className: string;
    text: string;
    width: number;
    right: number;
  }>;
};

const repoRoot = path.resolve(__dirname, "../../..");
const artifactsDir = path.join(repoRoot, "artifacts", "mobile-qa");
const refreshCookieNames = new Set(["zozi_refresh", "refresh_token"]);

const adminLogin: LoginConfig = {
  username: "admin@zozi.com",
  password: "admin123",
  landingRoute: "/admin/dashboard",
  expectedUrl: /\/admin\/dashboard(?:\?|$)/,
};

const supplierLogin: LoginConfig = {
  username: "supplier",
  password: "supplier123",
  landingRoute: "/supplier/dashboard",
  expectedUrl: /\/supplier\/dashboard(?:\?|$)/,
};

const logisticsLogin: LoginConfig = {
  username: "logistics",
  password: "logistics123",
  landingRoute: "/logistics-partner/dashboard",
  expectedUrl: /\/logistics-partner\/dashboard(?:\?|$)/,
};

const routeAudits: RouteAudit[] = [
  { label: "admin-dashboard", route: "/admin/dashboard", login: adminLogin },
  { label: "admin-email", route: "/admin/email", login: adminLogin },
  { label: "admin-audit-logs", route: "/admin/audit-logs", login: adminLogin },
  { label: "admin-logistics", route: "/admin/logistics", login: adminLogin },
  { label: "admin-barcode", route: "/admin/barcode", login: adminLogin },
  { label: "admin-suppliers", route: "/admin/suppliers", login: adminLogin },
  { label: "admin-users", route: "/admin/users", login: adminLogin },
  { label: "admin-orders", route: "/admin/orders", login: adminLogin },
  { label: "admin-commission", route: "/admin/commission", login: adminLogin },
  { label: "supplier-dashboard", route: "/supplier/dashboard", login: supplierLogin },
  { label: "supplier-orders", route: "/supplier/orders", login: supplierLogin },
  { label: "supplier-invoices", route: "/supplier/invoices", login: supplierLogin },
  { label: "supplier-payouts", route: "/supplier/payouts", login: supplierLogin },
  { label: "supplier-terms", route: "/supplier/terms", login: supplierLogin },
  { label: "logistics-dashboard", route: "/logistics-partner/dashboard", login: logisticsLogin },
  { label: "logistics-analytics", route: "/logistics-partner/analytics", login: logisticsLogin },
  { label: "logistics-payouts", route: "/logistics-partner/payouts", login: logisticsLogin },
  { label: "logistics-scan", route: "/logistics-partner/scan", login: logisticsLogin },
];

async function expectNavigation(page: Page, expectedUrl: RegExp, timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (expectedUrl.test(page.url())) {
      return;
    }
    await page.waitForTimeout(250);
  }

  throw new Error(`Timed out waiting for ${expectedUrl}, current URL: ${page.url()}`);
}

async function loginForAudit(page: Page, config: LoginConfig) {
  let lastError: unknown;

  for (let attempt = 0; attempt < 2; attempt += 1) {
    await page.context().clearCookies();

    try {
      const loginResponse = await page.context().request.post("/api/auth/login", {
        form: {
          username: config.username,
          password: config.password,
        },
      });

      if (!loginResponse.ok()) {
        throw new Error(`Audit login failed with ${loginResponse.status()}: ${await loginResponse.text()}`);
      }

      const loginBody = await loginResponse.json();
      if (!loginBody?.access_token) {
        throw new Error("Audit login did not return an access token.");
      }

      const cookies = await page.context().cookies();
      if (!cookies.some((cookie) => refreshCookieNames.has(cookie.name))) {
        throw new Error("Audit login did not set a refresh cookie.");
      }

      await page.addInitScript(() => {
        window.localStorage.setItem("zozi_has_session", "1");
      });

      await page.goto(config.landingRoute, { waitUntil: "domcontentloaded" });
      await expectNavigation(page, config.expectedUrl, 30_000);
      await page.waitForLoadState("networkidle");
      return;
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError instanceof Error ? lastError : new Error("Login failed during mobile audit.");
}

async function collectOverflowReport(page: Page, route: string): Promise<OverflowReport> {
  await page.goto(route, { waitUntil: "networkidle" });
  await page.waitForTimeout(500);

  return page.evaluate((currentRoute) => {
    const viewport = window.innerWidth;
    const scrollWidth = document.documentElement.scrollWidth;
    const hasOverflow = scrollWidth > viewport + 4;
    const offenders = hasOverflow
      ? Array.from(document.querySelectorAll("body *"))
          .map((element) => {
            const rect = element.getBoundingClientRect();
            const text = (element.textContent || "").replace(/\s+/g, " ").trim();
            return {
              tag: element.tagName.toLowerCase(),
              className: typeof element.className === "string" ? element.className.slice(0, 120) : "",
              text: text.slice(0, 80),
              width: Math.round(rect.width),
              right: Math.round(rect.right),
            };
          })
          .filter((item) => item.width > viewport + 4 || item.right > viewport + 4)
          .slice(0, 10)
      : [];

    return {
      route: currentRoute,
      viewport,
      scrollWidth,
      hasOverflow,
      offenders,
    };
  }, route);
}

async function attachAuditArtifacts(page: Page, testInfo: TestInfo, label: string, report: OverflowReport) {
  fs.mkdirSync(artifactsDir, { recursive: true });
  const screenshotPath = path.join(artifactsDir, `${label}.png`);
  const reportPath = path.join(artifactsDir, `${label}.json`);

  await page.screenshot({ path: screenshotPath, fullPage: true });
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  await testInfo.attach(`${label}-report`, {
    body: JSON.stringify(report, null, 2),
    contentType: "application/json",
  });
}

test.describe("mobile panel audit", () => {
  for (const audit of routeAudits) {
    test(`${audit.label} stays within the iPhone viewport`, async ({ page }, testInfo) => {
      test.slow();

      await loginForAudit(page, audit.login);
      const report = await collectOverflowReport(page, audit.route);
      await attachAuditArtifacts(page, testInfo, `${audit.label}-mobile`, report);

      expect(report.hasOverflow, JSON.stringify(report, null, 2)).toBe(false);
    });
  }
});
