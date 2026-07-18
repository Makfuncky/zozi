const adminEmail = process.env.DETOX_ADMIN_EMAIL || "admin@zozi.com";
const adminPassword = process.env.DETOX_ADMIN_PASSWORD || "admin123";

describe("Auth login smoke", () => {
  it("renders the native login surface and accepts input", async () => {
    await expect(element(by.id("auth-login-screen"))).toBeVisible();
    await expect(element(by.id("auth-login-identifier"))).toBeVisible();
    await expect(element(by.id("auth-login-password"))).toBeVisible();
    await expect(element(by.id("auth-login-submit"))).toBeVisible();

    await element(by.id("auth-login-identifier")).tap();
    await element(by.id("auth-login-identifier")).replaceText(adminEmail);
    await element(by.id("auth-login-password")).tap();
    await element(by.id("auth-login-password")).replaceText(adminPassword);

    await expect(element(by.id("auth-login-identifier"))).toHaveText(adminEmail);
  });

  it("authenticates into the protected admin dashboard and opens the orders tab", async () => {
    await element(by.id("auth-login-identifier")).replaceText(adminEmail);
    await element(by.id("auth-login-password")).replaceText(adminPassword);
    await device.pressBack();
    await element(by.id("auth-login-submit")).tap();

    await waitFor(element(by.id("admin-dashboard-screen"))).toBeVisible().withTimeout(20000);
    await expect(element(by.id("admin-dashboard-tab-analytics"))).toBeVisible();
    await expect(element(by.id("admin-dashboard-analytics-panel"))).toBeVisible();

    await element(by.id("admin-dashboard-tab-orders")).tap();
    await waitFor(element(by.id("admin-dashboard-orders-panel"))).toBeVisible().withTimeout(10000);
  });
});