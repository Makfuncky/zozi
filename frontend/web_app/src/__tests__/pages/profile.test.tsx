/**
 * Tests for profile page
 * Covers: redirect when not logged in, tab switching, form pre-fill
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { apiFetch } from "@/lib/api";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

let mockUser: any = null;
let mockIsLoggedIn = false;
let mockAuthLoading = false;

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({
    user: mockUser,
    isLoggedIn: mockIsLoggedIn,
    isLoading: mockAuthLoading,
    refresh: jest.fn(),
  }),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: jest.fn().mockResolvedValue({ ok: true, json: async () => ({}) }),
}));

jest.mock("@/lib/addressBook", () => ({
  stringifyAddressBook: jest.fn(() => ""),
  parseAddressBook: jest.fn(() => ({
    fullName: "", street: "", city: "", zip: "", country: "UAE",
    deliveryLocation: "", deliveryNote: "",
  })),
}));

jest.mock("@/lib/deliveryStore", () => ({
  useDeliveryStore: (sel: any) =>
    sel({
      setDetails: jest.fn(),
      initialize: jest.fn(),
      updateField: jest.fn(),
      hydrateFromAddressBook: jest.fn(),
    }),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (sel: any) => sel({ t: (k: string) => k }),
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...p }: any) => (
      <div {...p}>{children}</div>
    ),
    form: ({ children, ...p }: any) => (
      <form {...p}>{children}</form>
    ),
  },
}));

// ── Tests ────────────────────────────────────────────────────────────────────

import ProfilePage from "@/app/profile/page";

const mockApiFetch = apiFetch as jest.MockedFunction<typeof apiFetch>;

async function renderProfileAndWaitForReferralEffect() {
  render(<ProfilePage />);
  await waitFor(() => {
    expect(mockApiFetch).toHaveBeenCalledWith("/auth/referrals/me");
  });
  await waitFor(() => {
    expect(screen.getByText(/your referral code/i)).toBeInTheDocument();
  });
}

describe("ProfilePage — not logged in", () => {
  beforeEach(() => {
    mockUser = null;
    mockIsLoggedIn = false;
    mockAuthLoading = false;
    jest.clearAllMocks();
  });

  it("redirects to /login when user is not authenticated", async () => {
    render(<ProfilePage />);
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/login");
    });
  });
});

describe("ProfilePage — logged in", () => {
  beforeEach(() => {
    mockIsLoggedIn = true;
    mockAuthLoading = false;
    mockUser = {
      id: 1,
      username: "johndoe",
      email: "john@example.com",
      phone: "+1234567890",
      role: "customer",
      address_book: null,
    };
    mockApiFetch.mockImplementation(async (input) => {
      if (input === "/auth/referrals/me") {
        return {
          ok: true,
          json: async () => ({
            referral_code: "ZOZI123",
            referral_link: "https://zozi.example/r/ZOZI123",
            total_points: 0,
            referral_points: 0,
            sharing_points: 0,
            referred_count: 0,
            recent_activity: [],
          }),
        } as any;
      }

      return { ok: true, json: async () => ({}) } as any;
    });
    jest.clearAllMocks();
  });

  it("pre-fills the username field from the user object", async () => {
    await renderProfileAndWaitForReferralEffect();
    await waitFor(() => {
      const input = screen.getByDisplayValue("johndoe");
      expect(input).toBeInTheDocument();
    });
  });

  it("pre-fills the email field from the user object", async () => {
    await renderProfileAndWaitForReferralEffect();
    await waitFor(() => {
      expect(screen.getByDisplayValue("john@example.com")).toBeInTheDocument();
    });
  });

  it("shows a security tab option", async () => {
    await renderProfileAndWaitForReferralEffect();
    expect(screen.getByText(/security/i)).toBeInTheDocument();
  });
});


