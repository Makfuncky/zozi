jest.mock("@/lib/api", () => ({
  apiFetch: jest.fn().mockResolvedValue(
    new Response("{}", {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })
  ),
}));

import { useLocaleStore } from "@/lib/localeStore";

const { apiFetch: mockApiFetch } = jest.requireMock("@/lib/api") as {
  apiFetch: jest.Mock;
};

describe("localeStore", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.dir = "ltr";
    document.documentElement.lang = "en";
    useLocaleStore.setState({
      locale: "en",
      hasHydrated: false,
      t: (key) => key,
    });
    jest.clearAllMocks();
  });

  it("persists locale changes through /auth/me/preferences", async () => {
    useLocaleStore.getState().setLocale("ar");
    await useLocaleStore.getState().syncLocaleToServer();

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/auth/me/preferences",
      expect.objectContaining({
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preferred_language: "ar" }),
      })
    );
    expect(document.documentElement.lang).toBe("ar-OM");
    expect(document.documentElement.dir).toBe("rtl");
  });

  it("applies rtl direction for extended rtl locales", () => {
    useLocaleStore.getState().setLocale("ur");

    expect(document.documentElement.lang).toBe("ur-PK");
    expect(document.documentElement.dir).toBe("rtl");
  });

  it("hydrates the persisted locale after mount without relying on server render state", () => {
    window.localStorage.setItem(
      "zozi_locale",
      JSON.stringify({ state: { locale: "tr" }, version: 0 })
    );

    useLocaleStore.getState().hydrateLocale();

    expect(useLocaleStore.getState().locale).toBe("tr");
    expect(useLocaleStore.getState().hasHydrated).toBe(true);
    expect(document.documentElement.lang).toBe("tr-TR");
    expect(document.documentElement.dir).toBe("ltr");
  });
});
