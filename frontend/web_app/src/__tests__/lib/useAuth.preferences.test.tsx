import React from "react";
import { render, waitFor } from "@testing-library/react";

const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockApiFetch = jest.fn();
const mockGetAccessToken = jest.fn();
const mockSetAccessToken = jest.fn();
const mockClearAccessToken = jest.fn();

const localeState = {
  locale: "en",
  setLocale: jest.fn(),
};

const cartState = {
  syncOnLogin: jest.fn(),
  detachFromServer: jest.fn(),
};

const authModalState = {
  open: jest.fn(),
};

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  getAccessToken: (...args: unknown[]) => mockGetAccessToken(...args),
  setAccessToken: (...args: unknown[]) => mockSetAccessToken(...args),
  clearAccessToken: (...args: unknown[]) => mockClearAccessToken(...args),
}));

jest.mock("@/lib/localeStore", () => {
  const store: any = jest.fn();
  store.getState = () => localeState;
  return { useLocaleStore: store };
});

jest.mock("@/lib/cartStore", () => {
  const store: any = jest.fn();
  store.getState = () => cartState;
  return { useCartStore: store };
});

jest.mock("@/lib/authModalStore", () => {
  const store: any = jest.fn();
  store.getState = () => authModalState;
  return { useAuthModalStore: store };
});

import { AuthProvider } from "@/lib/useAuth";

describe("AuthProvider preference hydration", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem("zozi_has_session", "1");
    localeState.locale = "en";
    localeState.setLocale.mockClear();
    cartState.syncOnLogin.mockClear();
    cartState.detachFromServer.mockClear();
    mockPush.mockClear();
    mockReplace.mockClear();
    mockApiFetch.mockReset();
    mockGetAccessToken.mockReset();
    mockSetAccessToken.mockClear();
    mockClearAccessToken.mockClear();
    mockGetAccessToken.mockReturnValue(null);

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: process.env.TEST_ACCESS_TOKEN ?? "test-token" }),
    }) as unknown as typeof fetch;

    mockApiFetch.mockResolvedValue(
      new Response(
        JSON.stringify({
          id: 11,
          email: "prefs@zozi.test",
          username: "prefs-user",
          role: "customer",
          preferred_language: "ar",
          preferred_currency: "PKR",
          preferred_country: "PK",
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }
      )
    );
  });

  it("hydrates language preferences from /auth/me without overriding runtime currency detection", async () => {
    render(
      <AuthProvider>
        <div>child</div>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(mockSetAccessToken).toHaveBeenCalledWith("fresh-access-token");
      expect(mockApiFetch).toHaveBeenCalledWith("/auth/me");
      expect(localeState.setLocale).toHaveBeenCalledWith("ar");
      expect(cartState.syncOnLogin).toHaveBeenCalled();
    });
  });

  it("hydrates admin permission overrides for staff users", async () => {
    mockApiFetch.mockImplementation((url: unknown) => {
      if (url === "/admin/hierarchy/permissions") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              role: "admin",
              permissions: ["analytics.view"],
              matrix: {
                admin: ["analytics.view", "hierarchy.view"],
                sub_admin: ["analytics.view"],
              },
            }),
            {
              status: 200,
              headers: { "Content-Type": "application/json" },
            }
          )
        );
      }

      return Promise.resolve(
        new Response(
          JSON.stringify({
            id: 41,
            email: "admin@zozi.test",
            username: "admin-user",
            role: "admin",
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }
        )
      );
    });

    render(
      <AuthProvider>
        <div>child</div>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/auth/me");
      expect(mockApiFetch).toHaveBeenCalledWith("/admin/hierarchy/permissions");
      expect(JSON.parse(localStorage.getItem("zozi_admin_permission_overrides") || "null")).toEqual({
        admin: ["analytics.view", "hierarchy.view"],
        sub_admin: ["analytics.view"],
      });
    });
  });
});


