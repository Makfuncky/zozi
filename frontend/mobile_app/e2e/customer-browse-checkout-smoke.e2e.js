const customerEmail = process.env.DETOX_CUSTOMER_EMAIL || "customer@zozi.com";
const customerPassword = process.env.DETOX_CUSTOMER_PASSWORD || "customer123";

describe("Customer browse to checkout smoke", () => {
  it("logs in as a customer, browses a product, adds it to cart, and reaches payment step without postal code", async () => {
    await expect(element(by.id("auth-login-screen"))).toBeVisible();

    await element(by.id("auth-login-identifier")).replaceText(customerEmail);
    await element(by.id("auth-login-password")).replaceText(customerPassword);
    await device.pressBack();
    await element(by.id("auth-login-submit")).tap();

    await waitFor(element(by.id("products-screen"))).toBeVisible().withTimeout(20000);
    await waitFor(element(by.id("products-card-0"))).toBeVisible().withTimeout(20000);
    await element(by.id("products-card-0")).tap();

    await waitFor(element(by.id("product-detail-screen"))).toBeVisible().withTimeout(15000);
    await expect(element(by.id("product-detail-add-to-cart"))).toBeVisible();
    await element(by.id("product-detail-add-to-cart")).tap();

    await device.pressBack();
    await waitFor(element(by.id("products-screen"))).toBeVisible().withTimeout(10000);
    await element(by.id("products-header-cart")).tap();

    await waitFor(element(by.id("cart-screen"))).toBeVisible().withTimeout(15000);
    await expect(element(by.id("cart-proceed-checkout"))).toBeVisible();
    await element(by.id("cart-proceed-checkout")).tap();

    await waitFor(element(by.id("checkout-screen"))).toBeVisible().withTimeout(15000);
    await expect(element(by.id("checkout-coupon-input"))).toBeVisible();
    await expect(element(by.id("checkout-continue-to-shipping"))).toBeVisible();
    await element(by.id("checkout-continue-to-shipping")).tap();

    await waitFor(element(by.id("checkout-open-address-picker"))).toBeVisible().withTimeout(10000);
    await expect(element(by.id("checkout-full-name"))).toBeVisible();
    await element(by.id("checkout-zip")).replaceText("");
    await device.pressBack();
    await element(by.id("checkout-continue-to-payment")).tap();

    await waitFor(element(by.id("checkout-payment-method-cod"))).toBeVisible().withTimeout(10000);
    await expect(element(by.id("checkout-payment-method-card"))).toBeVisible();
    await expect(element(by.id("checkout-place-order"))).toBeVisible();
  });
});
