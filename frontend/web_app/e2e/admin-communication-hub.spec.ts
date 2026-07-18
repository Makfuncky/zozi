/**
 * Admin Communication Hub — Playwright E2E Tests
 *
 * Covers Video, Email, and Chat panels inside the unified
 * /admin/communication page. All backend calls are mocked.
 */
import { expect, test, type Page, type Route } from "@playwright/test";

const API_HOST = /https?:\/\/(?:localhost|127\.0\.0\.1):8000/;

type Room = {
  id: number;
  room_uuid: string;
  name: string;
  purpose: string;
  status: string;
  max_participants: number;
  country_code: string;
  created_at: string;
  invite_link: string;
};

type Campaign = {
  id: number;
  name: string;
  subject: string;
  status: string;
  sent_count: number;
  opened_count: number;
  created_at: string;
  country_code: string;
};

type Thread = {
  id: number;
  title: string;
  entity_type: string;
  entity_id: number;
  last_message: string;
  created_at: string;
};

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function mockAdminSession(page: Page) {
  await page.context().clearCookies();
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.evaluate(() => window.localStorage.removeItem("zozi_has_session")).catch(() => undefined);

  for (const candidate of ["admin@zozi.com", "admin"]) {
    const loginResponse = await page.request.post("/api/auth/login", {
      form: { username: candidate, password: "admin123" },
      failOnStatusCode: false,
    });
    if (!loginResponse.ok()) continue;

    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    await page.goto("/admin/communication", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const gate = page.getByRole("heading", { name: /Admin Access/i });
    const gateVisible = await gate.isVisible().catch(() => false);
    if (!gateVisible) {
      await page.route("**/cart/**", async (r) => fulfillJson(r, []));
      await page.route("**/notifications**", async (r) => fulfillJson(r, []));
      await page.route("**/api/notifications**", async (r) => fulfillJson(r, []));
      return;
    }
  }

  await page.goto("/admin/login", { waitUntil: "domcontentloaded", timeout: 120_000 });
  const submitBtn = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  await submitBtn.waitFor();
  const form = submitBtn.locator("xpath=ancestor::form[1]");
  const idInput = form.locator("input:not([type='password']):visible").first();
  await idInput.fill("admin@zozi.com");
  const pwInput = form.locator("input[type='password']:visible").first();
  await pwInput.fill("admin123");
  await submitBtn.click();
  await page.waitForTimeout(5000);
  await page.goto("/admin/communication", { waitUntil: "domcontentloaded", timeout: 120_000 });
  await page.route("**/cart/**", async (r) => fulfillJson(r, []));
  await page.route("**/notifications**", async (r) => fulfillJson(r, []));
  await page.route("**/api/notifications**", async (r) => fulfillJson(r, []));
}

test.describe("Admin Communication Hub", () => {
  let rooms: Room[];
  let campaigns: Campaign[];
  let threads: Thread[];

  test.beforeEach(async ({ page }) => {
    rooms = [
      {
        id: 1, room_uuid: "uuid-abc-123", name: "Q3 Board Review",
        purpose: "boardroom", status: "active", max_participants: 20,
        country_code: "AE", created_at: "2026-07-16T10:00:00Z",
        invite_link: "/meet/uuid-abc-123",
      },
      {
        id: 2, room_uuid: "uuid-def-456", name: "Sprint Planning",
        purpose: "meeting", status: "active", max_participants: 10,
        country_code: "AE", created_at: "2026-07-16T09:00:00Z",
        invite_link: "/meet/uuid-def-456",
      },
    ];

    campaigns = [
      {
        id: 1, name: "Summer Sale 2026", subject: "Don't miss our summer deals!",
        status: "sending", sent_count: 1200, opened_count: 450,
        created_at: "2026-07-15T08:00:00Z", country_code: "AE",
      },
    ];

    threads = [
      {
        id: 1, title: "Order #1234 Discussion", entity_type: "order",
        entity_id: 1234, last_message: "Please expedite shipping",
        created_at: "2026-07-16T07:00:00Z",
      },
    ];

    // Mock all comms API endpoints
    await page.route("**/admin/video/rooms", async (route) => {
      if (route.request().method() === "GET") {
        await fulfillJson(route, rooms);
      } else {
        // POST - create room
        const body = route.request().postDataJSON();
        const newRoom: Room = {
          id: 3, room_uuid: "uuid-new-789", name: body.name,
          purpose: body.purpose || "meeting", status: "active",
          max_participants: body.max_participants || 10,
          country_code: "AE", created_at: new Date().toISOString(),
          invite_link: "/meet/uuid-new-789",
        };
        rooms.push(newRoom);
        await fulfillJson(route, newRoom, 201);
      }
    });

    await page.route("**/admin/video/metrics", async (route) => {
      await fulfillJson(route, {
        total_rooms: rooms.length,
        active_rooms: rooms.filter((r) => r.status === "active").length,
        total_max_participants: rooms.reduce((s, r) => s + r.max_participants, 0),
      });
    });

    await page.route("**/admin/email/metrics", async (route) => {
      await fulfillJson(route, {
        total_subscribers: 5000,
        active_campaigns: 2,
        total_campaigns: campaigns.length,
        total_sent: campaigns.reduce((s, c) => s + c.sent_count, 0),
      });
    });

    await page.route("**/admin/email/campaigns/**", async (route) => {
      if (route.request().method() === "GET") {
        await fulfillJson(route, campaigns);
      } else {
        const body = route.request().postDataJSON();
        const newCampaign: Campaign = {
          id: campaigns.length + 1,
          name: body.name,
          subject: body.subject,
          status: "draft",
          sent_count: 0, opened_count: 0,
          created_at: new Date().toISOString(),
          country_code: "AE",
        };
        campaigns.push(newCampaign);
        await fulfillJson(route, newCampaign, 201);
      }
    });

    await page.route("**/admin/chat/threads", async (route) => {
      if (route.request().method() === "GET") {
        await fulfillJson(route, threads);
      } else {
        const url = new URL(route.request().url());
        const title = url.searchParams.get("title") || "New Thread";
        const newThread: Thread = {
          id: threads.length + 1,
          title,
          entity_type: url.searchParams.get("entity_type") || "admin",
          entity_id: 0,
          last_message: "",
          created_at: new Date().toISOString(),
        };
        threads.push(newThread);
        await fulfillJson(route, newThread, 201);
      }
    });

    await page.route("**/admin/chat/metrics", async (route) => {
      await fulfillJson(route, {
        total_threads: threads.length,
        total_messages: 50,
      });
    });

    // Auth + session
    await mockAdminSession(page);
  });

  // ═══════════════ Video Panel ═══════════════

  test("Video panel: displays rooms and supports create flow", async ({ page }) => {
    await page.getByRole("tab", { name: /video/i }).click();
    await page.waitForTimeout(1000);

    await expect(page.getByText("Secure Video Boardrooms")).toBeVisible();
    await expect(page.getByRole("button", { name: /create room/i })).toBeVisible();

    await page.getByRole("button", { name: /create room/i }).click();
    await expect(page.getByText("New Video Room")).toBeVisible({ timeout: 5000 });

    await page.getByPlaceholder(/Q3 Board Review/i).fill("E2E Test Room");
    await page.getByRole("button", { name: /create room/i }).last().click();
    await page.waitForTimeout(1000);

    await expect(page.getByText("E2E Test Room")).toBeVisible();
  });

  // ═══════════════ Email Panel ═══════════════

  test("Email panel: overview stats and campaign creation", async ({ page }) => {
    await page.getByRole("tab", { name: /email/i }).click();
    await page.waitForTimeout(1000);

    await expect(page.getByText(/subscribers|Emails Sent|Avg Open Rate/i)).toBeVisible();

    await page.getByRole("tab", { name: /campaigns/i }).click();
    await page.waitForTimeout(500);

    await page.getByRole("button", { name: /new campaign/i }).click();
    await expect(page.getByText("New Email Campaign")).toBeVisible({ timeout: 5000 });

    await page.getByPlaceholder(/e\.g\. Summer Sale/i).fill("E2E Campaign");
    await page.getByPlaceholder(/Don't miss/i).fill("E2E Subject Line");
    await page.getByRole("button", { name: /create campaign/i }).click();
    await page.waitForTimeout(1000);

    await expect(page.getByText("E2E Campaign")).toBeVisible();
  });

  // ═══════════════ Chat Panel ═══════════════

  test("Chat panel: displays threads and supports create flow", async ({ page }) => {
    await page.getByRole("tab", { name: /chat/i }).click();
    await page.waitForTimeout(1000);

    await expect(page.getByText(/threads/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /new/i })).toBeVisible();

    // Create a thread
    await page.getByRole("button", { name: /new/i }).click();
    await expect(page.getByText("New Chat Thread")).toBeVisible({ timeout: 5000 });

    await page.getByPlaceholder(/Order #1234/i).fill("E2E Thread");
    await page.getByRole("button", { name: /create thread/i }).click();
    await page.waitForTimeout(1000);

    await expect(page.getByText("E2E Thread")).toBeVisible();
  });
});
