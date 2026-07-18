import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const mockPush = jest.fn();
const mockPrefetch = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, prefetch: mockPrefetch, replace: jest.fn() }),
}));

jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ children, href, className }: any) => (
    <a href={href} className={className}>
      {children}
    </a>
  ),
}));

jest.mock("@/components/Logo", () => function LogoMock() {
  return <div data-testid="logo" />;
});

jest.mock("@/lib/api", () => ({
  apiFetch: jest.fn(),
  getErrorMessage: jest.fn((data) => data?.detail || ""),
  setAccessToken: jest.fn(),
  clearAccessToken: jest.fn(),
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({ refresh: jest.fn().mockResolvedValue({ role: "logistics_partner" }) }),
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

import LogisticsPartnerLoginPage from "@/app/logistics-partner/login/page";
import LogisticsPartnerRegisterPage from "@/app/logistics-partner/register/page";

describe("Logistics partner auth pages", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  it("shows the register entry point on the login page", () => {
    render(<LogisticsPartnerLoginPage />);

    expect(screen.getByRole("link", { name: /register/i })).toHaveAttribute(
      "href",
      "/logistics-partner/register"
    );
  });

  it("submits logistics partner registration and redirects back to login", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: 101 }),
    });

    render(<LogisticsPartnerRegisterPage />);

    fireEvent.change(screen.getByPlaceholderText(/choose a username/i), {
      target: { value: "dispatch_partner" },
    });
    fireEvent.change(screen.getByPlaceholderText(/partner@company.com/i), {
      target: { value: "partner@example.com" },
    });
    fireEvent.change(screen.getByPlaceholderText(/\+971 50 000 0000/i), {
      target: { value: "+971500000000" },
    });

    const passwordFields = screen.getAllByPlaceholderText(/••••••••/i);
    fireEvent.change(passwordFields[0], { target: { value: "PartnerPass123!" } });
    fireEvent.change(passwordFields[1], { target: { value: "PartnerPass123!" } });
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: /^register$/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/auth/register",
        expect.objectContaining({ method: "POST" })
      );
      expect(mockPush).toHaveBeenCalledWith("/logistics-partner/login?registered=1");
    });

    expect(global.fetch).toHaveBeenCalledWith(
      "/api/auth/register",
      expect.objectContaining({
        body: expect.stringContaining('"role":"logistics_partner"'),
      })
    );
  });
});


