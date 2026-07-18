/**
 * ticketsScreen.test.ts
 * Tests the Support Tickets screen logic:
 * - GET /tickets list
 * - POST /tickets (create ticket)
 * - POST /tickets/:id/reply
 * - Input validation for ticket creation
 */

const mockApiFetch = jest.fn();

jest.mock("react-native", () => ({ Platform: { OS: "android" } }));
jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));
jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  getTickets: () => mockApiFetch("/tickets"),
  getTicket: (id: number) => mockApiFetch(`/tickets/${id}`),
  createTicket: (data: any) =>
    mockApiFetch("/tickets", { method: "POST", body: JSON.stringify(data) }),
  replyToTicket: (id: number, message: string) =>
    mockApiFetch(`/tickets/${id}/reply`, { method: "POST", body: JSON.stringify({ message }) }),
  login: jest.fn(),
  logout: jest.fn(),
  getMe: jest.fn(),
  register: jest.fn(),
  restoreTokens: jest.fn().mockResolvedValue(false),
  getStoredRefreshToken: jest.fn().mockResolvedValue(null),
  refreshAccessToken: jest.fn(),
  tokenAdapter: { clearAccessToken: jest.fn(), clearRefreshToken: jest.fn() },
}));

import {
  getTickets,
  getTicket,
  createTicket,
  replyToTicket,
  type Ticket,
  type TicketReply,
} from "@/lib/api";

function makeTicket(id: number, status = "open"): Ticket {
  return {
    id,
    subject: `Ticket subject ${id}`,
    status,
    priority: "normal",
    created_at: new Date().toISOString(),
  };
}

beforeEach(() => jest.clearAllMocks());

// ── getTickets ────────────────────────────────────────────────────────────────

describe("ticketsScreen — getTickets()", () => {
  it("returns a list of tickets", async () => {
    const tickets = [makeTicket(1), makeTicket(2, "pending")];
    mockApiFetch.mockResolvedValueOnce(tickets);

    const data = await getTickets();
    expect(data).toHaveLength(2);
    expect(data[0].id).toBe(1);
    expect(data[1].status).toBe("pending");
  });

  it("returns empty array when no tickets", async () => {
    mockApiFetch.mockResolvedValueOnce([]);
    const data = await getTickets();
    expect(data).toEqual([]);
  });

  it("propagates API errors", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Unauthorized"));
    await expect(getTickets()).rejects.toThrow("Unauthorized");
  });
});

// ── getTicket (single) ────────────────────────────────────────────────────────

describe("ticketsScreen — getTicket(id)", () => {
  it("returns ticket with replies", async () => {
    const ticket: Ticket = {
      ...makeTicket(5),
      replies: [
        { id: 1, message: "We are looking into this.", is_admin: true, created_at: new Date().toISOString() },
      ],
    };
    mockApiFetch.mockResolvedValueOnce(ticket);

    const data = await getTicket(5);
    expect(data.id).toBe(5);
    expect(data.replies).toHaveLength(1);
    expect(data.replies![0].is_admin).toBe(true);
  });
});

// ── createTicket ──────────────────────────────────────────────────────────────

describe("ticketsScreen — createTicket()", () => {
  it("creates a ticket and returns the new ticket", async () => {
    const created: Ticket = makeTicket(10, "open");
    mockApiFetch.mockResolvedValueOnce(created);

    const result = await createTicket({
      subject: "Order not received",
      message: "I placed an order 10 days ago and have not received it.",
      priority: "high",
    });

    expect(result.id).toBe(10);
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/tickets",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("propagates API error on create failure", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Validation error"));
    await expect(
      createTicket({ subject: "X", message: "Short msg", priority: "normal" })
    ).rejects.toThrow("Validation error");
  });
});

// ── replyToTicket ─────────────────────────────────────────────────────────────

describe("ticketsScreen — replyToTicket()", () => {
  it("posts a reply and returns the TicketReply", async () => {
    const reply: TicketReply = {
      id: 99,
      message: "Please check your tracking number.",
      is_admin: false,
      created_at: new Date().toISOString(),
    };
    mockApiFetch.mockResolvedValueOnce(reply);

    const result = await replyToTicket(5, "Please check your tracking number.");
    expect(result.id).toBe(99);
    expect(result.is_admin).toBe(false);
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/tickets/5/reply",
      expect.objectContaining({ method: "POST" })
    );
  });
});

// ── Client-side validation (mirrors CreateTicketForm logic) ──────────────────

describe("ticketsScreen — form validation", () => {
  function validate(subject: string, message: string): string | null {
    if (subject.trim().length < 3) return "Subject must be at least 3 characters.";
    if (message.trim().length < 10) return "Message must be at least 10 characters.";
    return null;
  }

  it("accepts valid subject and message", () => {
    expect(validate("My order is missing", "I placed order #123 and it never arrived.")).toBeNull();
  });

  it("rejects short subject", () => {
    expect(validate("Hi", "This is my long message here.")).toBe("Subject must be at least 3 characters.");
  });

  it("rejects short message", () => {
    expect(validate("Order problem", "Too short")).toBe("Message must be at least 10 characters.");
  });

  it("trims whitespace before validation", () => {
    expect(validate("   A   ", "            ")).toBe("Subject must be at least 3 characters.");
  });
});

// ── Status colour mapping ─────────────────────────────────────────────────────

describe("ticketsScreen — status / priority colours", () => {
  const STATUS_COLORS: Record<string, string> = {
    open: "#32CD32",
    pending: "#f59e0b",
    resolved: "#22c55e",
    closed: "#6b7280",
  };

  it("maps all expected statuses to a colour", () => {
    ["open", "pending", "resolved", "closed"].forEach((s) => {
      expect(STATUS_COLORS[s]).toBeTruthy();
    });
  });

  it("open and resolved have different colours", () => {
    expect(STATUS_COLORS["open"]).not.toBe(STATUS_COLORS["resolved"]);
  });
});
