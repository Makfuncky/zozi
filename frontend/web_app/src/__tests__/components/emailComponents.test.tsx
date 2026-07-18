/**
 * Smoke tests for the four admin email management components.
 * Covers: EmailCampaignManager, EmailTemplateManager,
 *          EmailProviderConfigManager, EmailSuppressionManager
 */
import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";

// ── Shared mocks ──────────────────────────────────────────────────────────────

const mockAddToast = jest.fn();
jest.mock("@/lib/toastStore", () => ({
  useToastStore: (sel: any) => {
    const store = { addToast: mockAddToast };
    return typeof sel === "function" ? sel(store) : store;
  },
}));

jest.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_t, tag: string) =>
        ({ children, ...p }: any) =>
          React.createElement(tag, p, children),
    }
  ),
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Stub every icon to a plain span to avoid SVG import issues
jest.mock("@/lib/icons", () =>
  new Proxy(
    {},
    { get: (_t, name: string) => () => <span data-testid={`icon-${String(name)}`} /> }
  )
);

jest.mock("@/lib/backgroundJobs", () => ({
  trackBackgroundJob: jest.fn(),
  BackgroundJob: jest.fn(),
}));

jest.mock("@/lib/densityContext", () => ({
  useDensity: () => ({ density: "compact", setDensity: jest.fn() }),
  dc: (_d: any, compact: any, _normal: any, _expanded: any) => compact,
}));

jest.mock("@shared/components/EnterpriseDataTable", () => ({
  EnterpriseDataTable: ({ rows, columns, rowActions }: any) => (
    <table>
      <tbody>
        {(rows ?? []).map((row: any, i: number) => (
          <tr key={i}>
            {(columns ?? []).map((col: any) => (
              <td key={col.key}>{col.render ? col.render(row) : String(row[col.key] ?? "")}</td>
            ))}
            {rowActions && <td>{rowActions(row)}</td>}
          </tr>
        ))}
      </tbody>
    </table>
  ),
}));

jest.mock("@/components/admin/CreateCampaignForm", () => ({
  __esModule: true,
  default: () => <div data-testid="create-campaign-form" />,
}));

const mockApiFetch = jest.fn();
jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  getErrorMessage: (_err: unknown, fallback: string) => fallback,
  parseJsonResponse: async (res: any) => res.json(),
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeOkJson(data: unknown): Response {
  return {
    ok: true,
    json: async () => data,
    text: async () => JSON.stringify(data),
    status: 200,
  } as unknown as Response;
}

function makeErrorResponse(status = 500, text = "Server error"): Response {
  return {
    ok: false,
    json: async () => ({}),
    text: async () => text,
    status,
  } as unknown as Response;
}

beforeEach(() => {
  mockApiFetch.mockReset();
  mockAddToast.mockReset();
});

// ═════════════════════════════════════════════════════════════════════════════
// EmailCampaignManager
// ═════════════════════════════════════════════════════════════════════════════

import EmailCampaignManager from "@/components/admin/EmailCampaignManager";

const CAMPAIGNS = [
  {
    id: 1,
    name: "Spring Sale",
    subject: "Big spring discounts",
    status: "sent",
    send_at: null,
    sent_at: "2026-04-01T10:00:00Z",
    target_audience: "subscribers",
    recipient_count: 200,
    sent_count: 200,
    opened_count: 80,
    clicked_count: 30,
    created_at: "2026-03-30T08:00:00Z",
  },
  {
    id: 2,
    name: "Draft Newsletter",
    subject: "April updates",
    status: "draft",
    send_at: null,
    sent_at: null,
    target_audience: "all",
    recipient_count: 0,
    sent_count: 0,
    opened_count: 0,
    clicked_count: 0,
    created_at: "2026-04-02T08:00:00Z",
  },
];

describe("EmailCampaignManager", () => {
  it("renders loading state initially", () => {
    mockApiFetch.mockReturnValue(new Promise(() => {})); // never resolves
    render(<EmailCampaignManager />);
    // Component sets loading=true on mount; no campaign content yet
    expect(mockApiFetch).toHaveBeenCalledWith("/email/campaigns");
  });

  it("renders campaign list after successful fetch", async () => {
    mockApiFetch.mockResolvedValue(makeOkJson(CAMPAIGNS));
    render(<EmailCampaignManager />);
    await waitFor(() => {
      expect(screen.getByText("Spring Sale")).toBeInTheDocument();
    });
    expect(screen.getByText("Draft Newsletter")).toBeInTheDocument();
  });

  it("shows New Campaign button", async () => {
    mockApiFetch.mockResolvedValue(makeOkJson([]));
    render(<EmailCampaignManager />);
    const button = await screen.findByRole("button", { name: /new campaign/i });
    expect(button).toBeInTheDocument();
  });

  it("opens create-campaign form when New Campaign is clicked", async () => {
    mockApiFetch.mockResolvedValue(makeOkJson([]));
    render(<EmailCampaignManager />);
    const button = await screen.findByRole("button", { name: /new campaign/i });
    fireEvent.click(button);
    expect(screen.getByTestId("create-campaign-form")).toBeInTheDocument();
  });

  it("displays campaign status badge for sent campaigns", async () => {
    mockApiFetch.mockResolvedValue(makeOkJson(CAMPAIGNS));
    render(<EmailCampaignManager />);
    await waitFor(() => screen.getByText("Spring Sale"));
    // status badge text
    expect(screen.getByText("sent")).toBeInTheDocument();
  });

  it("handles fetch error gracefully (no crash)", async () => {
    mockApiFetch.mockRejectedValue(new Error("Network error"));
    expect(() => render(<EmailCampaignManager />)).not.toThrow();
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalled());
  });
});

// ═════════════════════════════════════════════════════════════════════════════
// EmailTemplateManager
// ═════════════════════════════════════════════════════════════════════════════

import EmailTemplateManager from "@/components/admin/EmailTemplateManager";

const TEMPLATES = [
  {
    id: 1,
    name: "Welcome Email",
    subject: "Welcome to ZOZI!",
    content: "<p>Hi {{first_name}}</p>",
    template_type: "welcome",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
  {
    id: 2,
    name: "Order Shipped",
    subject: "Your order is on its way",
    content: "<p>Shipped!</p>",
    template_type: "transactional",
    created_at: "2026-01-02T00:00:00Z",
    updated_at: "2026-01-02T00:00:00Z",
  },
];

describe("EmailTemplateManager", () => {
  it("fetches templates on mount", async () => {
    mockApiFetch.mockResolvedValue(makeOkJson(TEMPLATES));
    render(<EmailTemplateManager />);
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalledWith("/email/templates"));
  });

  it("renders template rows after load", async () => {
    mockApiFetch.mockResolvedValue(makeOkJson(TEMPLATES));
    render(<EmailTemplateManager />);
    await waitFor(() => screen.getByText("Welcome Email"));
    expect(screen.getByText("Order Shipped")).toBeInTheDocument();
  });

  it("shows New Template button", async () => {
    mockApiFetch.mockResolvedValue(makeOkJson([]));
    render(<EmailTemplateManager />);
    const btn = await screen.findByRole("button", { name: /new template/i });
    // Button is rendered regardless of data
    expect(btn).not.toBeNull();
  });

  it("calls DELETE endpoint when delete is confirmed", async () => {
    window.confirm = jest.fn(() => true);
    mockApiFetch
      .mockResolvedValueOnce(makeOkJson(TEMPLATES)) // initial load
      .mockResolvedValueOnce({ ok: true } as Response); // DELETE

    render(<EmailTemplateManager />);
    await waitFor(() => screen.getByText("Welcome Email"));

    // Find delete buttons — each template row has one
    const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
    fireEvent.click(deleteButtons[0]);

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith("/email/templates/1", { method: "DELETE" })
    );
  });

  it("handles empty template list without crash", async () => {
    mockApiFetch.mockResolvedValue(makeOkJson([]));
    render(<EmailTemplateManager />);
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalled());
    expect(screen.queryByText("Welcome Email")).toBeNull();
  });
});

// ═════════════════════════════════════════════════════════════════════════════
// EmailProviderConfigManager
// ═════════════════════════════════════════════════════════════════════════════

import EmailProviderConfigManager from "@/components/admin/EmailProviderConfigManager";

const RUNTIME_CONFIG = {
  id: 1,
  provider: "resend",
  active_provider: "resend",
  source: "db",
  available: true,
  live: true,
  preview_only: false,
  supports_webhooks: true,
  smtp_host: null,
  smtp_port: 587,
  smtp_username: null,
  smtp_use_tls: true,
  smtp_use_ssl: false,
  smtp_timeout_seconds: 15,
  email_from_default: "no-reply@zozi.com",
  email_from_promotional: "promo@zozi.com",
  email_from_transactional: "tx@zozi.com",
  email_from_notification: "noreply@zozi.com",
  email_from_alert: "alerts@zozi.com",
  email_from_verification: "verify@zozi.com",
  email_from_login_verification: "otp@zozi.com",
  email_from_password_reset: "reset@zozi.com",
  resend_api_key_configured: true,
  resend_webhook_secret_configured: true,
  smtp_password_configured: false,
};

describe("EmailProviderConfigManager", () => {
  it("fetches runtime config on mount", async () => {
    mockApiFetch.mockResolvedValue(makeOkJson(RUNTIME_CONFIG));
    render(<EmailProviderConfigManager />);
    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/email/config/runtime",
        expect.objectContaining({ disableCache: true })
      )
    );
  });

  it("renders provider selector after load", async () => {
    mockApiFetch.mockResolvedValue(makeOkJson(RUNTIME_CONFIG));
    render(<EmailProviderConfigManager />);
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalled());
    // Provider selector (select or radio group) should be present
    const providerSelect = screen.queryAllByRole("combobox");
    const providerRadios = screen.queryAllByRole("radio");
    expect(providerSelect.length > 0 || providerRadios.length > 0).toBe(true);
  });

  it("renders Save button", async () => {
    mockApiFetch.mockResolvedValue(makeOkJson(RUNTIME_CONFIG));
    render(<EmailProviderConfigManager />);
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalled());
    expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
  });

  it("calls PUT /email/config/runtime on save", async () => {
    mockApiFetch
      .mockResolvedValueOnce(makeOkJson(RUNTIME_CONFIG)) // initial load
      .mockResolvedValueOnce(makeOkJson(RUNTIME_CONFIG)); // save

    render(<EmailProviderConfigManager />);
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/email/config/runtime",
        expect.objectContaining({ method: "PUT" })
      )
    );
  });

  it("shows a toast on save error", async () => {
    mockApiFetch
      .mockResolvedValueOnce(makeOkJson(RUNTIME_CONFIG))
      .mockResolvedValueOnce(makeErrorResponse(500));

    render(<EmailProviderConfigManager />);
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => expect(mockAddToast).toHaveBeenCalled());
    const lastCall = mockAddToast.mock.calls[mockAddToast.mock.calls.length - 1];
    expect(lastCall[1]).toBe("error");
  });
});

// ═════════════════════════════════════════════════════════════════════════════
// EmailSuppressionManager
// ═════════════════════════════════════════════════════════════════════════════

import EmailSuppressionManager from "@/components/admin/EmailSuppressionManager";

const SUPPRESSIONS = [
  {
    id: 1,
    email: "bounced@example.com",
    reason: "bounce",
    source: "webhook",
    provider: "resend",
    status: "active",
    notes: null,
    suppressed_at: "2026-03-01T00:00:00Z",
    last_event_at: "2026-03-01T00:00:00Z",
  },
  {
    id: 2,
    email: "complaint@example.com",
    reason: "complaint",
    source: "webhook",
    provider: "resend",
    status: "active",
    notes: "Reported as spam",
    suppressed_at: "2026-03-10T00:00:00Z",
    last_event_at: "2026-03-10T00:00:00Z",
  },
];

describe("EmailSuppressionManager", () => {
  it("fetches suppressions with default active filter on mount", async () => {
    mockApiFetch.mockResolvedValue(makeOkJson(SUPPRESSIONS));
    render(<EmailSuppressionManager />);
    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith("/email/suppressions?status=active")
    );
  });

  it("renders email addresses after load", async () => {
    mockApiFetch.mockResolvedValue(makeOkJson(SUPPRESSIONS));
    render(<EmailSuppressionManager />);
    await waitFor(() => screen.getByText("bounced@example.com"));
    expect(screen.getByText("complaint@example.com")).toBeInTheDocument();
  });

  it("renders filter chips for all / active / inactive", async () => {
    mockApiFetch.mockResolvedValue(makeOkJson(SUPPRESSIONS));
    render(<EmailSuppressionManager />);
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalled());
    expect(screen.getByRole("button", { name: /all/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^active$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^inactive$/i })).toBeInTheDocument();
  });

  it("calls PATCH /email/suppressions/:id when Deactivate is clicked", async () => {
    mockApiFetch
      .mockResolvedValueOnce(makeOkJson(SUPPRESSIONS)) // fetch
      .mockResolvedValueOnce(
        makeOkJson({ ...SUPPRESSIONS[0], status: "inactive" }) // PATCH
      );

    render(<EmailSuppressionManager />);
    await waitFor(() => screen.getByText("bounced@example.com"));

    // Each active row shows a "Deactivate" button
    const deactivateButtons = screen.getAllByRole("button", { name: /deactivate/i });
    fireEvent.click(deactivateButtons[0]);

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/email/suppressions/1",
        expect.objectContaining({
          method: "PATCH",
          body: JSON.stringify({ status: "inactive" }),
        })
      )
    );
  });

  it("switches filter and re-fetches when All chip is clicked", async () => {
    mockApiFetch.mockResolvedValue(makeOkJson(SUPPRESSIONS));
    render(<EmailSuppressionManager />);
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: /all/i }));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith("/email/suppressions")
    );
  });

  it("shows error toast when PATCH fails", async () => {
    mockApiFetch
      .mockResolvedValueOnce(makeOkJson(SUPPRESSIONS))
      .mockResolvedValueOnce(makeErrorResponse(500, "Internal error"));

    render(<EmailSuppressionManager />);
    await waitFor(() => screen.getByText("bounced@example.com"));

    const deactivateButtons = screen.getAllByRole("button", { name: /deactivate/i });
    fireEvent.click(deactivateButtons[0]);

    await waitFor(() => expect(mockAddToast).toHaveBeenCalled());
    const lastCall = mockAddToast.mock.calls[mockAddToast.mock.calls.length - 1];
    expect(lastCall[1]).toBe("error");
  });
});


