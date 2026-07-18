/**
 * Tests for LoginClient — web_app login page
 * Tests form rendering, error display, and role-based redirects.
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";

expect.extend(toHaveNoViolations);

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockPrefetch = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace, prefetch: mockPrefetch }),
  useSearchParams: () => ({ get: () => null }),
}));

const mockRefresh = jest.fn();
const mockUseAuth = jest.fn(() => ({
  refresh: mockRefresh,
  user: null as { role: string } | null,
  isLoading: false,
}));
jest.mock("@/lib/useAuth", () => ({
  useAuth: () => mockUseAuth(),
}));

const mockApiFetch = jest.fn();
jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  parseJsonResponse: jest.fn(),
  getErrorMessage: jest.fn((d) => d?.detail || ""),
  setAccessToken: jest.fn(),
  clearAccessToken: jest.fn(),
}));

// Suppress OAuth provider fetch
global.fetch = jest.fn().mockResolvedValue({
  ok: true,
  json: async () => ({ google: false, facebook: false }),
}) as jest.Mock;

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (sel: any) => sel({ t: (k: string) => k }),
}));

jest.mock("@/components/Logo", () => function LogoMock() { return <div data-testid="logo" />; });

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

jest.mock("next/link", () =>
  function NextLinkMock({ children, href, ...rest }: any) { return <a href={href} {...rest}>{children}</a>; }
);

// ── Import after mocks ───────────────────────────────────────────────────────

import LoginClient from "@/app/login/LoginClient";

const { parseJsonResponse: mockParseJson } = jest.requireMock("@/lib/api");

async function renderLoginPage() {
  const view = render(<LoginClient />);
  await waitFor(() => {
    expect(global.fetch).toHaveBeenCalled();
  });
  return view;
}

function fillAndSubmit(username = "user@example.com", password = "password123") {
  fireEvent.change(screen.getByLabelText(/emailorusername|email or username/i), {
    target: { value: username },
  });
  fireEvent.change(screen.getByLabelText(/^password$/i), {
    target: { value: password },
  });
  fireEvent.click(screen.getByRole("button", { name: /signin|sign in|log in/i }));
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe("LoginClient", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      refresh: mockRefresh,
      user: null as { role: string } | null,
      isLoading: false,
    });
  });

  it("renders the email and password inputs", async () => {
    await renderLoginPage();
    expect(screen.getByLabelText(/emailorusername|email or username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
  });

  it("shows an error message on failed login (401)", async () => {
    const fakeRes = { ok: false, status: 401 };
    mockApiFetch.mockResolvedValueOnce(fakeRes);
    mockParseJson.mockResolvedValueOnce({ detail: "Invalid credentials" });

    await renderLoginPage();
    fillAndSubmit();

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  it("redirects admin user to /admin/dashboard", async () => {
    const fakeRes = { ok: true };
    mockApiFetch.mockResolvedValueOnce(fakeRes);
    mockParseJson.mockResolvedValueOnce({ access_token: "tok" });
    mockRefresh.mockResolvedValueOnce({ role: "admin" });

    await renderLoginPage();
    fillAndSubmit();

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/admin/dashboard");
    });
  });

  it("redirects supplier user to /supplier/dashboard", async () => {
    const fakeRes = { ok: true };
    mockApiFetch.mockResolvedValueOnce(fakeRes);
    mockParseJson.mockResolvedValueOnce({ access_token: "tok" });
    mockRefresh.mockResolvedValueOnce({ role: "supplier" });

    await renderLoginPage();
    fillAndSubmit();

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/supplier/dashboard");
    });
  });

  it("redirects logistics partner user to /logistics-partner/dashboard", async () => {
    const fakeRes = { ok: true };
    mockApiFetch.mockResolvedValueOnce(fakeRes);
    mockParseJson.mockResolvedValueOnce({ access_token: "tok" });
    mockRefresh.mockResolvedValueOnce({ role: "logistics_partner" });

    await renderLoginPage();
    fillAndSubmit();

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/logistics-partner/dashboard");
    });
  });

  it("redirects regular user to /", async () => {
    const fakeRes = { ok: true };
    const setItemSpy = jest.spyOn(Storage.prototype, "setItem");
    mockApiFetch.mockResolvedValueOnce(fakeRes);
    mockParseJson.mockResolvedValueOnce({ access_token: "tok" });
    mockRefresh.mockResolvedValueOnce({ role: "customer" });

    await renderLoginPage();
    fillAndSubmit();

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/");
    });
    expect(setItemSpy).toHaveBeenCalledWith("zozi_has_session", "1");
    setItemSpy.mockRestore();
  });

  it("shows error when refresh returns null (network error)", async () => {
    const fakeRes = { ok: true };
    mockApiFetch.mockResolvedValueOnce(fakeRes);
    mockParseJson.mockResolvedValueOnce({ access_token: "tok" });
    mockRefresh.mockResolvedValueOnce(null);

    await renderLoginPage();
    fillAndSubmit();

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  it("redirects authenticated users away from /login on render", async () => {
    mockUseAuth.mockReturnValue({
      refresh: mockRefresh,
      user: { role: "supplier" },
      isLoading: false,
    });

    await renderLoginPage();

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/supplier/dashboard");
    });
  });

  it("offers resend verification when login is blocked by email verification", async () => {
    mockApiFetch
      .mockResolvedValueOnce({ ok: false, status: 403 })
      .mockResolvedValueOnce({ ok: true, status: 200 });
    mockParseJson
      .mockResolvedValueOnce({
        detail: "Email address not verified. Please check your inbox and verify your email before logging in.",
      })
      .mockResolvedValueOnce({
        detail: "If an unverified account exists for that email or username, a verification email has been sent.",
      });

    await renderLoginPage();
    fillAndSubmit("customer3", "password123");

    const resendButton = await screen.findByRole("button", { name: /resendverificationemail/i });
    fireEvent.click(resendButton);

    await waitFor(() => {
      expect(screen.getByText(/verification email has been sent/i)).toBeInTheDocument();
    });
    expect(mockApiFetch).toHaveBeenNthCalledWith(
      2,
      "/auth/resend-verification/public",
      expect.objectContaining({
        method: "POST",
        skipAuthRedirect: true,
      })
    );
  });

  it("has no obvious accessibility violations on first render", async () => {
    const { container } = await renderLoginPage();
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});


