/**
 * Tests for help/tickets page
 * Covers: ticket form render, success state, error state, ticket list for logged-in users
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// ── Mocks ────────────────────────────────────────────────────────────────────

let mockIsLoggedIn = false;

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({ isLoggedIn: mockIsLoggedIn }),
}));

const mockApiFetch = jest.fn();
jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/userRealtime", () => ({
  connectUserRealtimeSocket: jest.fn(() => null),
  isTicketRealtimeMessage: jest.fn(() => false),
}));

jest.mock("@shared/realtime", () => ({
  createRealtimeRefreshScheduler: (refresh: () => void | Promise<void>) => ({
    cancel: jest.fn(),
    trigger: () => {
      void refresh();
    },
  }),
}));

jest.mock("framer-motion", () => ({
  motion: { div: ({ children, ...p }: any) => <div {...p}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// ── Tests ────────────────────────────────────────────────────────────────────

import HelpPage from "@/app/help/page";

describe("HelpPage — guest", () => {
  beforeEach(() => {
    mockIsLoggedIn = false;
    jest.clearAllMocks();
  });

  it("renders the ticket submission form", () => {
    render(<HelpPage />);
    expect(screen.getByLabelText(/subject/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/message/i)).toBeInTheDocument();
  });

  it("shows a login prompt for guests", () => {
    render(<HelpPage />);
    expect(screen.getByText(/please log in to submit a support ticket/i)).toBeInTheDocument();
  });
});

describe("HelpPage — logged in", () => {
  beforeEach(() => {
    mockIsLoggedIn = true;
    jest.clearAllMocks();
  });

  const waitForInitialTicketsLoad = async () => {
    await screen.findByText(/no tickets submitted yet/i);
  };

  it("shows success message after ticket submit", async () => {
    mockApiFetch
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 1, subject: "Help needed" }),
      })
      .mockResolvedValueOnce({ ok: true, json: async () => [] });

    render(<HelpPage />);

    await waitForInitialTicketsLoad();

    fireEvent.change(screen.getByLabelText(/subject/i), {
      target: { value: "I need help" },
    });
    fireEvent.change(screen.getByLabelText(/message/i), {
      target: { value: "Please assist me urgently." },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit|send/i }));

    await waitFor(() => {
      expect(screen.getByText(/ticket submitted|ticket created|received/i)).toBeInTheDocument();
    });
  });

  it("shows an error on API failure", async () => {
    mockApiFetch
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: "Validation error" }),
      });

    render(<HelpPage />);

    await waitForInitialTicketsLoad();

    fireEvent.change(screen.getByLabelText(/subject/i), {
      target: { value: "Issue" },
    });
    fireEvent.change(screen.getByLabelText(/message/i), {
      target: { value: "Something broke" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit|send/i }));

    await waitFor(() => {
      expect(screen.getByText(/failed|validation error/i)).toBeInTheDocument();
    });
  });

  it("fetches and displays existing tickets", async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        tickets: [
          {
            id: 1,
            subject: "My order is delayed",
            status: "open",
            priority: "normal",
            created_at: "2026-01-01",
          },
        ],
      }),
    });

    render(<HelpPage />);

    expect(await screen.findByText("My order is delayed")).toBeInTheDocument();
  });
});


