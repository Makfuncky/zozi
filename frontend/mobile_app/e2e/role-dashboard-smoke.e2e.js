const supplierEmail = process.env.DETOX_SUPPLIER_EMAIL || "supplier@zozi.com";
const supplierPassword = process.env.DETOX_SUPPLIER_PASSWORD || "supplier123";
const logisticsEmail = process.env.DETOX_LOGISTICS_EMAIL || "logistics@zozi.com";
const logisticsPassword = process.env.DETOX_LOGISTICS_PASSWORD || "logistics123";

async function loginAs(identifier, password) {
  await expect(element(by.id("auth-login-screen"))).toBeVisible();
  await element(by.id("auth-login-identifier")).replaceText(identifier);
  await element(by.id("auth-login-password")).replaceText(password);
  await device.pressBack();
  await element(by.id("auth-login-submit")).tap();
}

describe("Role dashboard smoke", () => {
  it("logs in as supplier and opens product management", async () => {
    await loginAs(supplierEmail, supplierPassword);

    await waitFor(element(by.id("supplier-dashboard-screen"))).toBeVisible().withTimeout(20000);
    await expect(element(by.id("supplier-dashboard-open-products"))).toBeVisible();
    await element(by.id("supplier-dashboard-open-products")).tap();

    await waitFor(element(by.id("supplier-products-screen"))).toBeVisible().withTimeout(15000);
  });

  it("logs in as logistics partner and opens shipments", async () => {
    await loginAs(logisticsEmail, logisticsPassword);

    await waitFor(element(by.id("logistics-dashboard-screen"))).toBeVisible().withTimeout(20000);
    await expect(element(by.id("logistics-dashboard-view-shipments"))).toBeVisible();
    await element(by.id("logistics-dashboard-view-shipments")).tap();

    await waitFor(element(by.id("logistics-shipments-screen"))).toBeVisible().withTimeout(15000);
  });
});