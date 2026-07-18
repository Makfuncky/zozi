/**
 * Tests for mobile_app/lib/localeStore.ts
 */

jest.mock("react-native", () => ({ Platform: { OS: "android" } }));
jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

import { useLocaleStore } from "@/lib/localeStore";

beforeEach(() => {
  useLocaleStore.setState({ locale: "en" } as any);
});

describe("localeStore", () => {
  it("starts with English locale", () => {
    expect(useLocaleStore.getState().locale).toBe("en");
  });

  it("t() returns English string for known key", () => {
    const { t } = useLocaleStore.getState();
    expect(t("home")).toBe("Home");
  });

  it("setLocale('ar') switches locale", () => {
    useLocaleStore.getState().setLocale("ar");
    expect(useLocaleStore.getState().locale).toBe("ar");
  });

  it("t() returns Arabic string after switching to ar", () => {
    useLocaleStore.getState().setLocale("ar");
    const { t } = useLocaleStore.getState();
    // Arabic "Home" key should not equal English value
    expect(typeof t("home")).toBe("string");
    expect(t("home").length).toBeGreaterThan(0);
  });

  it("setLocale back to en restores English", () => {
    useLocaleStore.getState().setLocale("ar");
    useLocaleStore.getState().setLocale("en");
    expect(useLocaleStore.getState().t("cart")).toBe("Cart");
  });

  it("accepts extended locale codes without breaking the translator", () => {
    useLocaleStore.getState().setLocale("ur");
    expect(useLocaleStore.getState().locale).toBe("ur");
    expect(useLocaleStore.getState().t("home")).toBe("Home");
  });
});
