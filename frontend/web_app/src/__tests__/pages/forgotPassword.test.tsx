/**
 * Tests for forgot-password page
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockApiFetch = jest.fn();
jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("next/link", () =>
  function NextLinkMock({ children, href }: any) { return <a href={href}>{children}</a>; }
);

// ── Tests ──────────────────────────────────────────────────────────────────────

import ForgotPasswordPage from "@/app/forgot-password/page";

describe("ForgotPasswordPage", () => {
  beforeEach(() => jest.clearAllMocks());

  it("renders the email input and submit button", () => {
    render(<ForgotPasswordPage />);
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /send|reset/i })).toBeInTheDocument();
  });

  it("shows success state after successful submission", async () => {
    mockApiFetch.mockResolvedValueOnce({ ok: true });

    render(<ForgotPasswordPage />);
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send|reset/i }));

    await waitFor(() => {
      expect(screen.getByText(/check your email/i)).toBeInTheDocument();
    });
  });

  it("shows error message when API returns an error", async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: "Email not found" }),
    });

    render(<ForgotPasswordPage />);
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: "nobody@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send|reset/i }));

    await waitFor(() => {
      expect(screen.getByText(/email not found/i)).toBeInTheDocument();
    });
  });

  it("shows network error on fetch failure", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("timeout"));

    render(<ForgotPasswordPage />);
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send|reset/i }));

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });
});


